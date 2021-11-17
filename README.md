# Exponea Software Engineer assignment

HTTP server with one endpoint `/api/smart` which sends a request to a backend service and returns its reponse.
In case of an error on the remote service is a log note stored into the _backend_errors.log_ file.


## Installation

The server requires the _aiohttp_ Python package. To run the server in production it's recommended to install _gunicorn_ too. The benchmark tool uses _matplotlib_. All dependencies are written in the _requirements.txt_ file and can be installed using

```shell
pip3 install -r requirements.txt
```


## How to run the app

There are two ways: directly running the "runserver.py" script or using Gunicorn.

The server can be run using the "runserver.py" script:

```shell
python runserver.py [-h] [--timeout TIMEOUT] [--limit LIMIT] [--port N [N ...]] remote
```

where the parameters are:

* *remote* (required) - Url address of the remote service
* *timeout* (seconds, optional) - Any HTTP request sent to the remote service will be forced to stop after this time period. Default value is 10 seconds.
* *limit* (optionsl) - Once LIMIT number of request are being processed at the moment the server will refuse any new requests. Default value is 100.
* *port* (optional) - Port on which to listen to. Default is 8000.

These parameters can also be set through environment variables: _REMOTE_URL_, _REQUEST_TIMEOUT_, _REQUESTS_LIMIT_ and _PORT_NUMBER_ respectively. _REMOTE_URL_, _REQUEST_TIMEOUT_, _REQUESTS_LIMIT_ are required to be set once using Gunicorn:

```shell
gunicorn runserver:app_factory -w [NUMBER_OF_WORKERS] -k aiohttp.GunicornWebWorker [--reload] --bind 0.0.0.0:[PORT]
```


## Using Docker

There are three Docker images: production (_Dockerfile_), development (_Dockerfile.develop_) and _Dockerfile.mockserver_ to run a mock backend service for development and testing.

For production run

```shell
docker-compose up -f docker-compose.yml
```

This passes following environment variables:

* REMOTE_URL=https://exponea-engineering-assignment.appspot.com/api/work
* REQ_TIMEOUT=5
* REQ_LIMIT=100
* WORKERS=8

For development run

```shell
docker-compose up -f docker-compose.develop.yml
```

This reads _USER_ID_ and _GROUP_ID_ environment variables (both default to 1000) and passes following environment variables to the main container:

* DEBUG=1
* REMOTE_URL=http://mock:8080
* REQ_TIMEOUT=5
* REQ_LIMIT=100
* PYTHONDONTWRITEBYTECODE=1
* PYTHONUNBUFFERED=1
* TEST_URL=http://localhost:8000

The _TEST_URL_ is required when running unit tests. It also sets up the mock backend server.


# The mock server

This server is designed to mimic `https://exponea-engineering-assignment.appspot.com/api/work` for developnent and test purposes. It can be given a scenario, i. e. list of N next response payloads and their time delays. It is strongly recommended to prepare a short response time scenario when using the benchmark tool.

## Running the mock server

```shell
python mockserver.py [-h] [--host N [N ...]] [--port N [N ...]]
```

The default port is _8080_.

## Mock server API

* `/` - Mimics the backend service behaviour.
* `/setscenario` - Accepts a JSON string in the request body. Structure of the JSON: _[["RESPONSE BODY", HTTP STATUS, DELAY in ms], [...], ...]_
* `/requests` - Returns a JSON string with a list of all HTTP requests' timestamps received since the last scenario setting.


# The benchmark tool

```shell
benchmark.py [-h] [--req N [N ...]] url
```

This tool increases the number of concurrent http requests to _url_ till the number _req_ / 10 (default value is 500). It produces a graph of the response time per one request for various concurrency values.

**This tool is supposed to be used in tandem with the mock server and after a proper scenario has been set.**

Sample Python code to set the scenario:

```python
import json
import os
import urllib.request

url = os.environ.get('REMOTE_URL') + '/setscenario'
scenario = 30000 * [['{"time":50}', 200, 50]]
payload = json.dumps(scenario)
req = urllib.request.Request(url, data=payload.encode())
res = urllib.request.urlopen(req).read() == b'OK'
```
