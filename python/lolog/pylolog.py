# pure python implementation of lolog, in case ctypes does not work

from __future__ import annotations

import collections
import contextvars
import enum
import fnmatch
import json
import re
import sys
import threading
import time
from typing import ClassVar, Optional, Any, Callable, Iterable, Dict, List, Tuple, TextIO


class Level(enum.IntEnum):
    NOTSET = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5
    SILENT = 6


StageType = Callable[["Config", "Record"], Optional["Record"]]


# list of (key, value) tuples -- but a different list per thread/task/
# greenlet/whatever concurrency abstraction is at play, as long as it works
# with contextvars!
_local_log_map: contextvars.ContextVar[List[Tuple[str, Any]]]
_local_log_map = contextvars.ContextVar('local_log_map')


class Config:
    # default instance, managed by init() and get_instance()
    _instance: ClassVar[Optional[Config]] = None

    mutex: threading.Lock
    log_map: List[Tuple[str, Any]]
    default_level: Level
    logger_level: Dict[str, Level]
    logger_patterns: List[Tuple[re.Pattern, Level]]
    stream: Optional[TextIO]
    pipeline: List[StageType]
    logger: Dict[str, Logger]
    time: Callable[[], float]

    def __init__(self):
        self.mutex = threading.Lock()
        self.log_map = []
        self.default_level = Level.NOTSET
        self.logger_level = {}
        self.logger_patterns = []
        self.stream = None
        self.pipeline = []
        self.logger = {}
        self.time = time.time

    def configure(
            self, level: Level = Level.DEBUG,
            format: str = "simple",
            stream: TextIO = sys.stderr,
    ) -> None:
        self.default_level = level

        # setup the pipeline
        if level is not None:
            self.add_stage(filter_level)
        if format is not None:
            if format not in FORMATTER:
                raise ValueError('unsupported format: {!r}'.format(format))
            self.add_stage(FORMATTER[format])
        if stream is not None:
            self.stream = stream
            self.add_stage(output_stream)

    def set_default_level(self, level: Level) -> None:
        self.default_level = level

    def add_value(self, key: str, value: Any) -> None:
        self.log_map.append((key, value))

    def add_local_value(self, key: str, value: Any) -> None:
        try:
            local = _local_log_map.get()
        except LookupError:
            local = []
            _local_log_map.set(local)
        local.append((key, value))

    def get_log_map(self) -> List[Tuple[str, Any]]:
        return self.log_map

    def get_local_log_map(self) -> List[Tuple[str, Any]]:
        try:
            return _local_log_map.get()
        except LookupError:
            return []

    def clear_local_log_map(self) -> None:
        _local_log_map.set([])

    def set_logger_level(self, name: str, level: Level) -> None:
        self.logger_level[name] = level

    def set_logger_pattern_level(self, pattern: str, level: Level) -> None:
        regex = re.compile(fnmatch.translate(pattern))
        self.logger_patterns.append((regex, level))

    def get_logger_level(self, name: str) -> Level:
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

    def add_stage(self, stage: StageType) -> None:
        try:
            stage.mut           # type: ignore
            stage.fmt           # type: ignore
            stage.out           # type: ignore
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
    'Record', ['time', 'name', 'level', 'message', 'log_map', 'outbuf'])


class Logger:
    def __init__(self, config: Config, name: str):
        self.config = config
        self.name = name
        self.log_map: List[Tuple[str, Any]] = []

    def __str__(self):
        return '{}'.format(self.name)

    def __repr__(self):
        return '<{} at 0x{:x}: {}>'.format(
            self.__class__.__name__, id(self), self)

    def add_global_value(self, key: str, value: Any) -> None:
        self.config.add_value(key, value)

    def add_local_value(self, key: str, value: Any) -> None:
        self.config.add_local_value(key, value)

    def add_value(self, key: str, value: Any) -> None:
        self.log_map.append((key, value))

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log(Level.DEBUG, message, kwargs.items())

    def info(self, message: str, **kwargs: Any) -> None:
        self._log(Level.INFO, message, kwargs.items())

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log(Level.WARNING, message, kwargs.items())

    def error(self, message: str, **kwargs: Any) -> None:
        self._log(Level.ERROR, message, kwargs.items())

    def critical(self, message: str, **kwargs: Any) -> None:
        self._log(Level.CRITICAL, message, kwargs.items())

    def _log(self, level: Level, message: str, items: Iterable[Tuple[str, Any]]) -> None:
        config = self.config

        log_map = [
            *config.get_log_map(),
            *config.get_local_log_map(),
            *self.log_map,
            *items,
        ]
        record: Optional[Record]
        record = Record(
            time=config.time(),
            name=self.name,
            level=level,
            message=message,
            log_map=log_map,
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
    config.configure(level=level, format=format, stream=stream)

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
    ] + record.log_map
    data = ['{}={}'.format(key, value() if callable(value) else value)
            for (key, value) in items]
    record.outbuf.append(' '.join(data) + '\n')
    return record


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            iterable = iter(obj)
        except TypeError:
            return str(obj)
        else:
            return list(iterable)


_json_encoder = JSONEncoder()


@stage(fmt=True)
def format_json(config: Config, record: Record) -> Optional[Record]:
    items = [
        ('time', isotime(record.time)),
        ('name', record.name),
        ('level', record.level.name),
        ('message', record.message),
    ] + record.log_map
    data = {key: value() if callable(value) else value
            for (key, value) in items}
    record.outbuf.append(_json_encoder.encode(data) + '\n')
    return record


FORMATTER = {
    'simple': format_simple,
    'json': format_json,
}


@stage(out=True)
def output_stream(config: Config, record: Record) -> Optional[Record]:
    if not record.outbuf:
        raise RuntimeError(
            'lolog pipeline error: '
            'cannot output log record that has not been formatted')
    if config.stream is None:
        raise RuntimeError(
            'lolog pipeline error: '
            'cannot output log record when config.stream is not set')

    config.stream.write(''.join(record.outbuf))
    return record


# aliases for compatibility with C interface
make_config = Config
make_logger = Logger
