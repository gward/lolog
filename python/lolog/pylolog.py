# pure python implementation of lolog, in case ctypes does not work

from __future__ import annotations

import collections
import enum
import fnmatch
import re
import sys
import threading
import time
from typing import ClassVar, Optional, Any, Callable, Dict, List, Tuple, TextIO


class Level(enum.IntEnum):
    NOTSET = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5
    SILENT = 6


StageType = Callable[["Config", "Record"], Optional["Record"]]


class Config:
    # default instance, managed by init() and get_instance()
    _instance: ClassVar[Optional[Config]] = None

    mutex: threading.Lock
    context: List[Tuple[str, str]]
    local: threading.local
    default_level: Level
    logger_level: Dict[str, Level]
    logger_patterns: List[Tuple[re.regex, Level]]
    pipeline: List[StageType]
    logger: Dict[str, Logger]
    time: Callable[[], float]

    def __init__(self):
        self.mutex = threading.Lock()
        self.context = []
        self.local = threading.local()
        self.default_level = Level.NOTSET
        self.logger_level = {}
        self.logger_patterns = []
        self.pipeline = []
        self.logger = {}
        self.time = time.time

    def set_default_level(self, level: Level):
        self.default_level = level

    def add_context(self, key, value):
        self.context.append((key, value))

    def add_local_context(self, key, value):
        self.get_local_context().append((key, value))

    def get_context(self) -> List[Tuple[str, str]]:
        return self.context

    def get_local_context(self) -> List[Tuple[str, str]]:
        try:
            return self.local.context
        except AttributeError:
            self.local.context = []
            return self.local.context

    def clear_local_context(self):
        del self.local.context

    def set_logger_level(self, name: str, level: Level):
        self.logger_level[name] = level

    def set_logger_pattern_level(self, pattern: str, level: Level):
        regex = re.compile(fnmatch.translate(pattern))
        self.logger_patterns.append((regex, level))

    def get_logger_level(self, name: str):
        if name in self.logger_level:
            # this logger has been explicitly configured
            return self.logger_level[name]

        # search for a matching pattern
        for (regex, level) in self.logger_patterns:
            if regex.match(name):
                return level
        else:
            # fallback to default
            return self.default_level

        return self.logger_level.get(name, self.default_level)

    def add_stage(self, stage: StageType):
        try:
            stage.mut
            stage.fmt
            stage.out
        except AttributeError:
            raise TypeError(
                'pipeline stage must provide attrs mut, fmt, and out')

        self.pipeline.append(stage)

    def get_logger(self, name: str) -> Logger:
        with self.mutex:
            if name not in self.logger:
                self.logger[name] = Logger(self, name)
            return self.logger[name]


Record = collections.namedtuple(
    'Record', ['time', 'name', 'level', 'message', 'context', 'outbuf'])


class Logger:
    def __init__(self, config: Config, name: str):
        self.config = config
        self.name = name
        self.context: List[Tuple[str, str]] = []

    def __str__(self):
        return '{}'.format(self.name)

    def __repr__(self):
        return '<{} at 0x{:x}: {}>'.format(
            self.__class__.__name__, id(self), self)

    def add_global_context(self, key: str, value):
        self.config.add_context(key, value)

    def add_local_context(self, key: str, value):
        self.config.add_local_context(key, value)

    def add_context(self, key, value):
        self.context.append((key, value))

    def debug(self, message: str, **kwargs):
        self._log(Level.DEBUG, message, kwargs.items())

    def info(self, message: str, **kwargs):
        self._log(Level.INFO, message, kwargs.items())

    def _log(self, level: Level, message: str, items: List[Tuple[str, Any]]):
        config = self.config

        context = [
            *config.get_context(),
            *config.get_local_context(),
            *self.context,
            *items,
        ]
        record = Record(
            time=config.time(),
            name=self.name,
            level=level,
            message=message,
            context=context,
            outbuf=[])

        for stage in config.pipeline:
            record = stage(config, record)
            if record is None:
                break


def isotime(now):
    return (time.strftime('%FT%T', time.localtime(now)) +
            '{:06f}'.format(now % 1)[1:])


def init(level: Level = Level.DEBUG,
         format: str = "simple",
         stream: TextIO = sys.stderr) -> Config:
    config = get_config()
    if config.pipeline:
        raise RuntimeError(
            'lolog has already been initialized; '
            'use get_config() to configure it more')

    config.default_level = level

    # setup the pipeline
    if level is not None:
        config.add_stage(filter_level)
    if format is not None:
        config.add_stage(FORMATTER[format])
    if stream is not None:
        @stage(out=True)
        def output_stream(config: Config, record: Record) -> Optional[Record]:
            if not record.outbuf:
                raise RuntimeError(
                    'lolog pipeline error: '
                    'cannot output log record that has not been formatted')

            stream.write(''.join(record.outbuf))
            return record

        config.add_stage(output_stream)

    return config


def get_config() -> Config:
    if Config._instance is None:
        Config._instance = Config()
    return Config._instance


def get_logger(name):
    return get_config().get_logger(name)


def stage(mut=False, fmt=False, out=False):
    def wrap(func):
        func.mut = mut
        func.fmt = fmt
        func.out = out
        return func

    return wrap


@stage()
def filter_level(config: Config, record: Record) -> Optional[Record]:
    """filter log records based on level"""
    if config.get_logger_level(record.name) <= record.level:
        return record
    return None


@stage(fmt=True)
def format_simple(config: Config, record: Record) -> Optional[Record]:
    items = [
        ('time', isotime(record.time)),
        ('name', record.name),
        ('level', record.level.name),
        ('message', record.message),
    ] + record.context
    data = ['{}={}'.format(key, value() if callable(value) else value)
            for (key, value) in items]
    record.outbuf.append(' '.join(data) + '\n')
    return record


FORMATTER = {
    "simple": format_simple,
}


# aliases for compatibility with C interface
make_config = Config
make_logger = Logger
