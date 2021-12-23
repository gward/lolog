#!venv/bin/python

# informal test of a multithreaded app using lolog
#
# expectations:
#
# * every line will include the thread ID twice, as tid1=T and tid2=T --
#   the two values will always be the same
#
# * for each thread (i.e. each distinct value of tid), the value of count
#   will always be the same -- we will not accidentally log thread A's
#   count in thread B
#
# * for each thread, iter will always increment from 1 to count, and then
#   the thread will stop

import random
import sys
import threading

import lolog


def main():
    lolog.init(stream=sys.stdout)

    num_threads = 10
    log = lolog.get_logger("myapp.mt")

    def worker(name):
        count = random.randint(10, 20)
        tid = threading.current_thread().ident
        log.add_local_context("tid1", tid)
        log.add_local_context("count", count)
        for idx in range(1, count + 1):
            log.info("doing some work", iter=idx, tid2=tid)

    log.info("starting multithreaded test", num_threads=num_threads)
    threads = []
    for idx in range(num_threads):
        name = f"thread {idx}"
        thread = threading.Thread(target=worker, name=name, args=(name,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
