"""informal manual test of interception"""

import logging
import lolog
import lolog.iclogging

#log = logging.getLogger()


def main():
    cfg = lolog.init()
    lolog.iclogging.intercept(cfg)

    logging.getLogger().info("info message to root logger")

    logging.getLogger("foo").debug("debug message to foo")
    logging.getLogger("foo.bar").info("info message with arg %s", "meep")
    logging.getLogger("foo.baz").debug("debug with arg %s and kwargs %(bar)s",
                                       "blip", bar=42)


main()

