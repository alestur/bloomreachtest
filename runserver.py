import argparse
import os

from aiohttp import web

from server.classes import ServerHandler


PORT_NUMBER = os.environ.get('PORT_NUMBER', 8000)
REMOTE_URL = os.environ.get('REMOTE_URL')
REQUEST_TIMEOUT = os.environ.get('REQ_TIMEOUT')
REQUESTS_LIMIT = os.environ.get('REQ_LIMIT')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the webserver.')

    parser.add_argument('remote', type=str,
        help='Remote url'
    )
    parser.add_argument('--timeout', type=str,
        help='Maxmim time in seconds to wair for remote response.'
    )
    parser.add_argument('--limit', type=str,
        help='Number of request the server is cat process concurrently.'
    )
    parser.add_argument('--port', metavar='N', type=int, nargs='+',
        help='Port number'
    )

    args = parser.parse_args()
    kwargs = {}

    if args.port:
        PORT_NUMBER = args.port[0]
    if args.remote:
        REMOTE_URL = args.remote
    if args.timeout:
        REQUEST_TIMEOUT = args.timeout[0]
    if args.limit:
        REQUESTS_LIMIT = args.limit[0]


async def app_factory():
    handler = ServerHandler(
        REMOTE_URL,
        request_timeout=REQUEST_TIMEOUT,
        requests_limit=REQUESTS_LIMIT,
    )

    server = web.Application()
    server.add_routes([
        web.get('/api/smart', handler.handle_smart),
        web.get('/api/smart/{timeout}', handler.handle_smart),
    ])

    return server


if __name__ == '__main__':
    web.run_app(app_factory(), port=PORT_NUMBER)
