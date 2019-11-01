#!venv/bin/python

# prototype of the Python interface to lolog

import enum
import io
import sys
import time
from typing import Optional, List, Tuple


class Level(enum.IntEnum):
    NOTSET = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5
    SILENT = 6


class Config:
    default_level: Level
    outfile: io.TextIOBase      # writeable file

    def __init__(
            self,
            default_level: Level,
            outfile: io.TextIOBase):
        self.default_level = default_level
        self.outfile = outfile
        self.context = []

    def add_context(self, key, value):
        self.context.append((key, value))


class Logger:
    config: Optional[Config]

    def __init__(
            self,
            name: str,
            level: Level,
            context: List[Tuple[str, str]]):
        self.name = name
        self.level = level
        self.context = context
        self.config = None

    def __str__(self):
        return "{} ({})".format(self.name, self.level.name)

    def __repr__(self):
        return "<{} at 0x{:x}: {}>".format(
            self.__class__.__name__, id(self), self)

    def add_context(self, key, value):
        self.context.append((key, value))

    def debug(self, message: str, **items):
        self._log(Level.DEBUG, message, **items)

    def info(self, message: str, **items):
        self._log(Level.INFO, message, **items)

    def _log(self, level: Level, message: str, **items):
        if self.config is None:
            self.config = get_config()
        assert self.config is not None       # make mypy happy
        if self.level is Level.NOTSET:
            self.level = self.config.default_level
        if level < self.level:
            return

        all_items = self.config.context + self.context + [
            ("level", str(level.name[0])),
            ("name", self.name),
            ("message", message),
        ]
        all_items += items.items()
        data = ["{}={}".format(key, value() if callable(value) else value)
                for (key, value) in all_items]

        self.config.outfile.write(" ".join(data) + "\n")


def isotime():
    now = time.time()
    return (time.strftime("%FT%T", time.localtime(now)) +
            "{:06f}".format(now % 1)[1:])


_config = None


def configure_logging(default_level: Level, outfile: io.TextIOBase):
    global _config
    config = Config(default_level, outfile)
    _config = config
    return _config


def get_config() -> Config:
    global _config
    if _config is None:
        configure_logging(Level.NOTSET, sys.stdout)
    return _config


def get_logger(name):
    return Logger(name, Level.NOTSET, [])


def main():
    applog = get_logger("myapp")
    liblog = get_logger("lib.guts")
    print(f"applog = {applog!r}, liblog = {liblog!r}")

    config = get_config()
    config.add_context("time", isotime)

    liblog.level = Level.INFO

    liblog.debug("this is a really chatty library", arg1="bla", arg2="hi")
    applog.debug("hello from the app")
    print(f"applog = {applog!r}, liblog = {liblog!r}")

    liblog.info("stupid library blathering away",
                a="meeeeeeep", b="deeeeeeeep", c="piiiiiiing")
    applog.add_context("request_id", "244a")
    applog.info("useful info from the app")



if __name__ == "__main__":
    main()

