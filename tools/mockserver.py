import argparse
import asyncio
import random
import time

from aiohttp import web


class MockHandler:
    """HTTP request handler designed to mimic
    https://exponea-engineering-assignment.appspot.com/api/work
    for developnent and test purposes.
    """

    def __init__(self):
        self.requests = []
        self.scenario = None
        self.start_time = time.perf_counter()

    async def handle_get(self, request):
        if self.scenario and len(self.scenario) > len(self.requests):
            body, status, delay = self.scenario[len(self.requests)]
        else:
            delay = float(random.randint(100, 600))
            mode = random.randint(0, 10)

            if mode > 9:
                body = ''
                status = 0
                delay = 10000.0
            elif mode > 8:
                body = 'Not a valid JSON'
                status = 200
            elif mode > 7:
                body = 'Not a valid JSON'
                status = 500
            else:
                body = '{"time": %d}' % (delay)
                status = 200

        self.requests.append(time.perf_counter() - self.start_time)

        print('STATUS: {:d}\tUPTIME: {:0.4f}\t{:0.0f}\t{}'.format(
            status,
            time.perf_counter() - self.start_time,
            delay,
            body,
        ))
        await asyncio.sleep(delay / 1000.0)

        if status == 200:
            return web.Response(
                body=body,
                headers={
                    'Content-type': 'application/json',
                }
            )
        else:
            raise web.HTTPInternalServerError()

    async def handle_requests(self, request):
        return web.json_response(self.requests)

    async def handle_scenario(self, request):
        data = await request.json()
        self.set_scenario(data)

        return web.Response(body='OK')

    def set_scenario(self, scenario):
        """Prepare next responses according to test's assumtions.

        :param scenario: a list of (body, status, delay) tuples
        """
        self.requests = []
        self.scenario = scenario
        self.start_time = time.perf_counter()


mock_handler = MockHandler()

mock_server = web.Application()
mock_server.add_routes([
    web.get('/', mock_handler.handle_get),
    web.get('/requests', mock_handler.handle_requests),
    web.post('/setscenario', mock_handler.handle_scenario),
])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a webserver for testing.')

    parser.add_argument('--host', metavar='N', type=int, nargs='+',
        help='Host url'
    )
    parser.add_argument('--port', metavar='N', type=int, nargs='+',
        help='Port number'
    )

    args = parser.parse_args()
    kwargs = {}

    if args.host:
        kwargs['host'] = args.host[0]
    if args.port:
        kwargs['port'] = args.port[0]

    web.run_app(mock_server, **kwargs)
