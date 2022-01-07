import asyncio
import logging

from aiohttp import web

from .functions import fetch
from .functions import perform_tasks


class ProcCounter:
    """
    Set an asyncio.Event when either all coroutines
    are unsuccessful or none is running.
    """

    def __init__(self, ceiling = 1):
        self.ceiling = ceiling
        self.event = asyncio.Event()
        self.n = 0

    def __on_change(self):
        if self.n == 0 and not self.event.is_set():
            self.event.set()
        elif self.n >= self.ceiling and not self.event.is_set():
            self.event.set()

    def register(self):
        self.n += 1
        self.__on_change()

    def unregister(self):
        self.n = max(self.n - 1, 0)
        self.__on_change()


class ServerHandler:

    def __init__(self, remote_url, *args, **kwargs):
        logging.basicConfig(
            filename='./backend_errors.log',
            format='%(asctime)s %(message)s',
            encoding='utf-8',
            level=logging.WARNING
        )

        self.pending_requests = 0
        self.remote_url = remote_url
        self.requests_limit  = int(kwargs.get('requests_limit') or 100)
        self.req_timeout = int(kwargs.get('request_timeout') or 10)

    async def handle_smart(self, request):
        if self.pending_requests > self.requests_limit:
            raise web.HTTPTooManyRequests()
        else:
            self.pending_requests += 1

        # Query request object for the timeout parameter.
        if request.match_info.get('timeout'):
            timeout = float(request.match_info.get('timeout')) / 1000.0
        else:
            timeout = request.query.get('timeout')

        requests = 3
        pr_cnt = ProcCounter(requests)
        result = {
            'data': {},
            'status': None,
        }
        tasks = []
        url = self.remote_url

        for i in range(requests):
            delay = 300 if i else 0
            coro = fetch(url, result, pr_cnt, self.req_timeout, delay)
            tasks.append(asyncio.create_task(coro))

        try:
            await asyncio.wait_for(
                perform_tasks(tasks),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            e = 'No successful response within timeout ({} ms).'.format(timeout)
            logging.warning(e)
            result['data'] = {
                'error': e,
            }
            result['status'] = 500

        # Cancel pending tasks.
        for task in tasks:
            if not (task.done() or task.cancelled()):
                task.cancel()

        self.pending_requests -= 1

        if result['status'] == 200:
            return web.json_response(result['data'])
        else:
            raise web.HTTPInternalServerError()
