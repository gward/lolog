#!venv/bin/python

# prototype of the Python interface to lolog

import random
import sys
import threading

import lolog


def main():
    config = lolog.get_config()
    config.set_outfile(sys.stdout)
    config.add_context("time", lolog.isotime)
    config.set_logger_level("lib.guts", lolog.Level.INFO)

    simple_test()
    mt_test()


def simple_test():
    print("** START simple_test() **")
    applog = lolog.get_logger("myapp")
    liblog = lolog.get_logger("lib.guts")
    print(f"applog = {applog!r}, liblog = {liblog!r}")

    liblog.debug("this is a really chatty library", arg1="bla", arg2="hi")
    applog.debug("hello from the app")
    print(f"applog = {applog!r}, liblog = {liblog!r}")

    liblog.info("stupid library blathering away",
                a="meeeeeeep", b="deeeeeeeep", c="piiiiiiing")
    applog.add_context("request_id", "244a")
    applog.info("useful info from the app")

    assert lolog.get_logger("myapp") is applog

    subliblog = lolog.get_logger("lib.guts.deep")
    subliblog.debug("this sublib is also noisy", arg="!!!")
    print("** END simple_test() **")


def mt_test():
    print("** START mt_test() **")

    num_threads = 10
    log = lolog.get_logger("myapp.mt")
    log.add_context("threads", str(num_threads))

    def worker(name):
        tid = threading.current_thread().ident
        count = random.randint(10, 20)
        for idx in range(1, count + 1):
            message = f"message {idx}/{count} from {name} ({tid})"
            log.info(message, idx=idx, count=count)

    threads = []
    for idx in range(num_threads):
        name = f"thread {idx}"
        thread = threading.Thread(target=worker, name=name, args=(name,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    print("** END mt_test() **")


if __name__ == "__main__":
    main()

