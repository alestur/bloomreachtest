import aiohttp
import asyncio
import json
import logging


async def fetch(url, result, pr_cnt, req_timeout, delay=0):
    """Fetch resource from url asynchronously. Only a valid JSON with
    HTTP status 200 is accepted. In case of unsuccessful response wait
    till other coroutines finish.
    Uses the value of req_timeout on each request.

    :param url: Url
    :param result: Dictionary-like object to store response data
    :param pr_cnt: ProcCounter instance
    :param req_timeout: Stop any request after req_timeout seconds.
    :param delay: Number of ms to wait before the request is sent
    :return: None
    """
    await asyncio.sleep(delay / 1000.0)

    if result.get('status') != 200:
        async with aiohttp.ClientSession(conn_timeout=req_timeout) as session:
            async with session.get(url) as response:
                if result.get('status') != 200:
                    try:
                        result['data'] = await response.json()
                        result['status'] = response.status
                    except (
                        aiohttp.client_exceptions.ContentTypeError,
                        json.decoder.JSONDecodeError,
                    ):
                        pr_cnt.register()
                        logging.warning('Service returned an invalid JSON.')
                else:
                    logging.warning('Service returned HTTP status {}'.format(
                        result.get('status'),
                    ))

        if result['status'] != 200:
            await pr_cnt.event.wait()


async def perform_tasks(tasks):
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
    )
