import aiohttp
import argparse
import asyncio
import time

import matplotlib.pyplot as plt


async def fetch_url(session, url):
    async with session.get(url) as resp:
        return await resp.text()


def print_results(total_time, results):
    n = len(results)
    N = 0

    for r in results:
        N += r['N']

    print('Total time {} requests took: {}'.format(N, total_time))
    print('Average time per request: {}'.format(N / total_time))

    plt.scatter([i['n'] for i in results], [i['tpr'] for i in results])
    plt.show()


async def run(url, requests, results):
    """Benchmark remote url with increasing number of concurrent
    requests.
    """
    is_run = True
    n = 1
    N = 0

    while is_run:
        print('Current concurrency: {}...'.format(n))

        async with aiohttp.ClientSession() as session:
            time_start = time.perf_counter()
            for i in range(requests // n):
                tasks = []

                for j in range(n):
                    tasks.append(asyncio.create_task(fetch_url(session, url)))

                N += n
                await asyncio.gather(*tasks)
            time_stop = time.perf_counter()

        print('\t...{} seconds'.format(time_stop - time_start))
        results.append({
            'n': n,
            'N': N,
            't': time_stop - time_start,
            'tpr': (time_stop - time_start) / N,
        })
        n += 1

        if n > requests // 10:
            is_run = False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Benchmark a HTTP server.')

    parser.add_argument('url', type=str,
        help='Remote url'
    )
    parser.add_argument('--req', metavar='N', type=int, nargs='+',
        help='Number requests to be sent (default 500).'
    )

    args = parser.parse_args()
    url = args.url or 'http://localhost'
    requests = args.req[0] if args.req else 500
    results = []

    total_time_start = time.perf_counter()
    asyncio.run(run(url, requests, results))
    total_time_stop = time.perf_counter()

    print_results(total_time_stop - total_time_start, results)
