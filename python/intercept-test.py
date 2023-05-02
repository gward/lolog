"""informal manual test of interception"""

import logging
import lolog
import lolog.iclogging

log = logging.getLogger()


def main():
    logging.basicConfig(level=logging.DEBUG)
    log.info("info to root before interception")

    cfg = lolog.init()
    icept = lolog.iclogging.Interceptor(cfg, logging.Logger)
    icept.intercept()

    log.info("info message to root logger")

    logging.getLogger("foo").debug("debug message to foo")
    logging.getLogger("foo.bar").info("info message with arg %s", "meep")
    logging.getLogger("foo.baz").debug("debug with arg %s and kwargs %(bar)s",
                                       "blip", bar=42)  # type: ignore # kwarg

    icept.undo()

    log.info("info to root after undo")


main()
