#!venv/bin/python

# informal test of an asyncio app using lolog
#
# expectations:
#
# * for each task, the value of count will always be the same -- we will
#   not accidentally log task A's count in task B
#
# * for each task, iter will always increment from 1 to count, and then
#   the thread will stop

import asyncio
import random
import sys

import lolog

log = lolog.get_logger('aio-test')


async def main():
    lolog.init(stream=sys.stdout)

    num_tasks = 10
    log.info('starting asyncio test', num_tasks=num_tasks)
    tasks = []
    for idx in range(num_tasks):
        count = random.randint(10, 20)
        tasks.append(asyncio.create_task(worker(idx, count)))
        log.debug('created task', idx=idx, task=tasks[-1])

    log.debug('gathering tasks')
    await asyncio.gather(*tasks)
    log.info('all done')


async def worker(worker_id, count):
    log.add_local_context('wid1', worker_id)
    for idx in range(1, count + 1):
        log.info('doing some work', iter=idx, wid2=worker_id)
        await asyncio.sleep(random.uniform(0.001, 0.050))


asyncio.run(main())
