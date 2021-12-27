#!venv/bin/python

# informal test of concurrency using eventlet

import random
import sys

import eventlet
import eventlet.green.threading

import lolog
import lolog.pylolog

# similar to eventlet.monkey_patch, but laser focused on pylolog -- but it
# would probably be even better if pylolog used eventlet.corolocal.local
# directly
lolog.pylolog.threading = eventlet.green.threading

log = lolog.get_logger('eventlet-test')


def main():
    lolog.init(stream=sys.stdout)

    num_gthreads = 10
    log.info('starting eventlet test', num_gthreads=num_gthreads)
    inputs = []
    for idx in range(num_gthreads):
        count = random.randint(10, 20)
        inputs.append((idx, count))

    pool = eventlet.GreenPool()
    for _ in pool.imap(worker, inputs):
        pass
    log.info('all done')


def worker(input):
    (worker_id, count) = input
    log.add_local_context('wid1', worker_id)
    log.info('starting worker', count=count)
    for idx in range(1, count + 1):
        log.info('doing some work', iter=idx, wid2=worker_id)
        eventlet.sleep(random.uniform(0.001, 0.050))


main()
