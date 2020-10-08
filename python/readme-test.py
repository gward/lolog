import os
import sys
import lolog

log = lolog.get_logger("main")


def main():
    lolog.init(level=lolog.INFO, format="simple", stream=sys.stdout)
    log.add_context("pid", os.getpid())
    log.info("starting up", prog=sys.argv[0])
    log.debug("detailed debug info", foo=42, thing="blah")


main()
