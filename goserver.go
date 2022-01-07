package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"sync"
	"time"
)

type TimeResponse struct {
	MS int `json:"time"`
}

func FetchRemote(i int, wg *sync.WaitGroup, url string, ch chan<- TimeResponse, clear chan struct{}) {
	var s []byte
	var t TimeResponse

	defer wg.Done()

	if i > 0 {
		time.Sleep(300 * time.Millisecond)
	}

	select {
	case <-clear:
		return
	default:
		var err error

		fmt.Println("Sending a request...")

		res, err := http.Get(url)

		if err != nil {
			fmt.Fprintf(os.Stderr, "%2d ERROR:\t%s\n", i, err)
			return
		}

		defer res.Body.Close()

		if s, err = ioutil.ReadAll(res.Body); err != nil {
			fmt.Fprintf(os.Stderr, "%2d READ ERROR:\t%s\n", i, err)
			return
		}

		if err = json.Unmarshal(s, &t); err != nil {
			fmt.Fprintf(os.Stderr, "%02d JSON ERROR:\t%s\n", i, err)
			return
		}

		ch <- t
		clear <- struct{}{}
		clear <- struct{}{}
	}
}

func main() {
	var host = flag.String("host", "localhost", "Listening host")
	maxRequests := 100
	pendingRequest := 0
	var port = flag.Int("port", 8000, "Listening port")
	var url = flag.String("url", "https://exponea-engineering-assignment.appspot.com/api/work", "Remote service url")

	n := 3
	flag.Parse()

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
		fmt.Fprint(w, "Not a valid path. Try '/api/smart' or /api/smart?timeout=MILLISECONDS.")
	})

	http.HandleFunc("/api/smart", func(w http.ResponseWriter, r *http.Request) {
		ch := make(chan TimeResponse, n+2)
		clear := make(chan struct{}, n)
		var err error
		isDone := false
		t0 := time.Now()
		var timeout time.Duration
		var wg sync.WaitGroup

		// Refuse to accept too many requests at once.
		if pendingRequest > maxRequests {
			w.WriteHeader(http.StatusTooManyRequests)
			return
		}
		pendingRequest++
		defer func() { pendingRequest-- }()

		query := r.URL.Query().Get("timeout")
		if timeout, err = time.ParseDuration(fmt.Sprintf("%sms", query)); err != nil {
			timeout = time.Duration(1000 * time.Millisecond)
		}

		defer func() { isDone = true }()

		for i := 0; i < n; i++ {
			wg.Add(1)
			go FetchRemote(i, &wg, *url, ch, clear)
		}

		// Force a HTTP response after the timeout period. TimeResponse.MS=-1 signals that the request has failed.
		go func() {
			time.Sleep(time.Duration(timeout))
			if !isDone {
				fmt.Fprintf(os.Stderr, "FAIL: No successful response within timeout (%v).\n", timeout)
				w.WriteHeader(http.StatusInternalServerError)
				fmt.Fprintf(w, "No successful response within timeout (%v).", timeout)
				ch <- TimeResponse{MS: -1}
			}
		}()

		// Send a failed response once all concurrent remote requests have failed. TimeResponse.MS=-1 signals that the request has failed.
		go func() {
			wg.Wait()
			if !isDone {
				fmt.Fprintf(os.Stderr, "FAIL: No successful response out of %d attempts.\n", n)
				w.WriteHeader(http.StatusInternalServerError)
				fmt.Fprintf(w, "No successful response out of %d attempts.", n)
				ch <- TimeResponse{MS: -1}
			}
		}()

		// Respond with the first valid JSON returned from the remote service.
		if res := <-ch; res.MS > 0 {
			fmt.Printf("Got %+v after %d ms.\n", res, time.Since(t0).Milliseconds())
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(res)
		}
	})

	fmt.Printf("Remote service set to '%s'.\n", *url)
	fmt.Printf("Listening on %s:%d...\n", *host, *port)

	log.Fatal(http.ListenAndServe(fmt.Sprintf("%s:%d", *host, *port), nil))
}
