#!venv/bin/python

# informal testing of concurrency using gevent

import random
import sys

import gevent
import gevent.monkey

import lolog

gevent.monkey.patch_thread()
log = lolog.get_logger('gevent-test')


def main():
    lolog.init(stream=sys.stdout)

    num_tasks = 10
    tasks = []
    log.info('starting gevent test', num_tasks=num_tasks)
    for idx in range(num_tasks):
        count = random.randint(10, 20)
        tasks.append(gevent.spawn(worker, idx, count))

    gevent.joinall(tasks)


def worker(worker_id, count):
    log.add_local_context('wid1', worker_id)
    log.info('starting worker', count=count)
    for idx in range(1, count + 1):
        log.info('doing some work', iter=idx, wid2=worker_id)
        gevent.sleep(random.uniform(0.001, 0.050))


main()
