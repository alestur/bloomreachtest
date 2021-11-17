import json
import os
import time
import unittest
import urllib.parse
import urllib.request


def setUpModule():
    """Try to set a test scenario. Stop testing in case that
    the remote service is not the mock server.
    """
    remote_url = os.environ.get('REMOTE_URL')
    req = urllib.request.Request(
        remote_url + '/setscenario',
        data=json.dumps([]).encode(),
    )

    try:
        res = urllib.request.urlopen(req)
        res = urllib.request.urlopen(remote_url + '/requests')
    except:
        exit('The mock server is not running. Stopping tests.')


def tearDownModule():
    remote_url = os.environ.get('REMOTE_URL')
    req = urllib.request.Request(
        remote_url + '/setscenario',
        data=json.dumps([]).encode(),
    )


def read_requests():
    """Obtain a request log from the mock server."""
    remote_url = os.environ.get('REMOTE_URL')
    res = urllib.request.urlopen(remote_url + '/requests')

    return json.loads(res.read())


def set_scenario(scenario):
    """Send scenario as a JSON object to the mock server in order to
    prepare responses for the next test.
    """
    remote_url = os.environ.get('REMOTE_URL')
    req = urllib.request.Request(
        remote_url + '/setscenario',
        data=json.dumps(scenario).encode(),
    )

    return urllib.request.urlopen(req).read() == 'OK'


# Create your tests here.
class UnitTests(unittest.TestCase):

    def setUp(self):
        self.url = os.environ.get('TEST_URL', 'http://localhost:8000/api/smart')

    def tearDown(self):
        pass

    def test_PathSmart_Not404(self):
        r = urllib.request.urlopen(self.url)

        self.assertNotEqual(r.code, 404)

    def test_PathSmart_ResponseIsJson(self):
        set_scenario([
            ('{"time": 100}', 200, 100),
        ])

        r = urllib.request.urlopen(self.url)

        self.assertEqual(r.read().decode(), '{"time": 100}')

    def test_PathSmart_Timeout(self):
        timeout = 200
        set_scenario([
            ('Too late', 200, 600),
            ('Too late', 200, 600),
            ('Too late', 200, 600),
        ])

        start_time = time.perf_counter()
        with self.assertRaises(urllib.error.HTTPError):
            r = urllib.request.urlopen(self.url + '/' + str(timeout))
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(len(requests), 1)
        self.assertAlmostEqual(
            stop_time - start_time,
            timeout / 1000.0,
            delta=0.2,
        )

    def test_PathSmart_TimeoutExtreme(self):
        timeout = 20
        set_scenario([
            ('Too late', 200, 320),
            ('Too late', 200, 10),
            ('Too late', 200, 10),
        ])

        start_time = time.perf_counter()
        with self.assertRaises(urllib.error.HTTPError):
            r = urllib.request.urlopen(self.url + '/' + str(timeout))
        stop_time = time.perf_counter()

        requests = read_requests()

        self.assertEqual(len(requests), 1)

    def test_PathSmart_TimeoutLong(self):
        timeout = 500
        set_scenario([
            ('{"time": 1000}', 200, 1000),
            ('{"time": 1000}', 200, 1000),
            ('{"time": 1000}', 200, 1000),
        ])

        start_time = time.perf_counter()
        with self.assertRaises(urllib.error.HTTPError):
            r = urllib.request.urlopen(self.url + '/' + str(timeout))
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(len(requests), 3)
        self.assertAlmostEqual(stop_time - start_time, 0.5, delta=0.1)

    def test_PathSmart_Under300ms_OnlyOneRequestSent(self):
        set_scenario([
            ('{"time": 100}', 200, 290),
            ('{"time": 10}', 200, 10),
            ('{"time": 10}', 200, 10),
        ])

        start_time = time.perf_counter()
        r = urllib.request.urlopen(self.url)
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(r.code, 200)
        self.assertEqual(r.read().decode(), '{"time": 100}')
        self.assertEqual(len(requests), 1)
        self.assertAlmostEqual(stop_time - start_time, 0.3, delta=0.1)

    def test_PathSmart_RequestInterval(self):
        set_scenario([
            ('{"time": 300}', 200, 301),
            ('{"time": 300}', 200, 300),
            ('{"time": 300}', 200, 300),
        ])

        start_time = time.perf_counter()
        r = urllib.request.urlopen(self.url)
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(r.code, 200)
        self.assertEqual(r.read().decode(), '{"time": 300}')
        self.assertEqual(len(requests), 3)
        self.assertAlmostEqual(requests[1] - requests[0], 0.3, delta=0.02)
        self.assertAlmostEqual(requests[2] - requests[1], 0.0, delta=0.02)

    def test_PathSmart_FirstInvalidJson_ThreeRequests(self):
        set_scenario([
            ('Invalid response', 200, 10),
            ('{"time": 210}', 200, 210),
            ('{"time": 100}', 200, 100),
        ])

        start_time = time.perf_counter()
        r = urllib.request.urlopen(self.url)
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(r.code, 200)
        self.assertEqual(r.read().decode(), '{"time": 100}')
        self.assertEqual(len(requests), 3)
        self.assertAlmostEqual(stop_time - start_time, 0.4, delta=0.2)

    def test_PathSmart_FirstInvalidStatus_ThreeRequests(self):
        set_scenario([
            ('{"time": 10}', 500, 10),
            ('{"time": 210}', 200, 210),
            ('{"time": 100}', 200, 100),
        ])

        start_time = time.perf_counter()
        r = urllib.request.urlopen(self.url)
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(r.code, 200)
        self.assertEqual(r.read().decode(), '{"time": 100}')
        self.assertEqual(len(requests), 3)
        self.assertAlmostEqual(stop_time - start_time, 0.4, delta=0.2)

    def test_PathSmart_FirstInvalidStatus_UseFirstToCome(self):
        set_scenario([
            ('{"time": 210}', 500, 10),
            ('{"time": 210}', 200, 210),
            ('{"time": 100}', 200, 100),
        ])

        start_time = time.perf_counter()
        r = urllib.request.urlopen(self.url)
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(r.code, 200)
        self.assertEqual(r.read().decode(), '{"time": 100}')
        self.assertEqual(len(requests), 3)
        self.assertAlmostEqual(stop_time - start_time, 0.4, delta=0.2)

    def test_PathSmart_SecondInvalidStatus_UseFirstToCome(self):
        set_scenario([
            ('{"time": 400}', 200, 400),
            ('{"time": 210}', 500, 50),
            ('{"time": 100}', 200, 200),
        ])

        start_time = time.perf_counter()
        r = urllib.request.urlopen(self.url)
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(r.code, 200)
        self.assertEqual(r.read().decode(), '{"time": 400}')
        self.assertEqual(len(requests), 3)
        self.assertAlmostEqual(stop_time - start_time, 0.4, delta=0.2)

    def test_PathSmart_AllInvalidJson_MaxTime(self):
        """All remote responses are invalid but arrive in the given time."""
        set_scenario([
            ('Invalid response', 200, 600),
            ('{"time": 210}', 500, 300),
            ('Invalid response', 200, 400),
        ])

        start_time = time.perf_counter()
        with self.assertRaises(urllib.error.HTTPError):
            r = urllib.request.urlopen(self.url)
        stop_time = time.perf_counter()
        requests = read_requests()

        self.assertEqual(len(requests), 3)
        self.assertAlmostEqual(stop_time - start_time, 0.7, delta=0.8)


if __name__ == '__main__':
    unittest.main()
