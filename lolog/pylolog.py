# pure python implementation of lolog, in case ctypes does not work

from __future__ import annotations

import contextvars
import enum
import fnmatch
import json
import re
import sys
import threading
import time
import typing as ty
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
LogMap = List[Tuple[str, Any]]


# list of (key, value) tuples -- but a different list per thread/task/
# greenlet/whatever concurrency abstraction is at play, as long as it works
# with contextvars!
_local_log_map: contextvars.ContextVar[LogMap]
_local_log_map = contextvars.ContextVar('local_log_map')


class Config:
    # default instance, managed by init() and get_instance()
    _instance: ClassVar[Optional[Config]] = None

    mutex: threading.Lock
    log_map: LogMap
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
            self,
            level: Level = Level.DEBUG,
            format: ty.Union[str, StageType] = "simple",
            stream: TextIO = sys.stderr,
    ) -> None:
        self.default_level = level

        # setup the pipeline
        if isinstance(format, str):
            if format not in FORMATTER:
                raise ValueError('unsupported format: {!r}'.format(format))
            self.add_stage(FORMATTER[format])
        elif callable(format):
            self.add_stage(format)
        elif format is not None:
            raise TypeError('unsupported format: must be str or callable')

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

    def get_log_map(self) -> LogMap:
        return self.log_map

    def get_local_log_map(self) -> LogMap:
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

    def insert_stage(self, before_idx: int, stage: StageType) -> None:
        self.pipeline.insert(before_idx, stage)

    def add_stage(self, stage: StageType) -> None:
        self.pipeline.append(stage)

    def get_logger(self, name: str) -> Logger:
        with self.mutex:
            if name not in self.logger:
                self.logger[name] = Logger(self, name)
            return self.logger[name]

    def format_time(self, time_: float) -> str:
        return (time.strftime('%FT%T', time.localtime(time_)) +
                '{:06f}'.format(time_ % 1)[1:])


class Record(ty.NamedTuple):
    time: float
    name: str
    level: Level
    message: str
    log_map: LogMap
    outbuf: List[str]

    def get_items(self) -> LogMap:
        items = [
            ('name', self.name),
            ('level', self.level.name),
        ]
        for (key, value) in self.log_map:
            if callable(value):
                value = value()
            items.append((key, value))
        return items

    def replace(self, **kwargs: Any) -> Record:
        return self._replace(**kwargs)


class Logger:
    def __init__(self, config: Config, name: str):
        self.config = config
        self.name = name
        self.log_map: LogMap = []

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

        if level < config.get_logger_level(self.name):
            return

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


def init(level: Level = Level.DEBUG,
         format: ty.Union[str, StageType] = "simple",
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


def format_simple(config: Config, record: Record) -> Optional[Record]:
    append = record.outbuf.append
    append('{} {}'.format(config.format_time(record.time), record.message))
    for (key, value) in record.get_items():
        append(' {}={}'.format(key, value))
    append('\n')
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


def format_json(config: Config, record: Record) -> Optional[Record]:
    items = record.get_items()
    data = {
        'time': config.format_time(record.time),
        'message': record.message,
    }
    data.update(items)
    record.outbuf.append(_json_encoder.encode(data) + '\n')
    return record


FORMATTER = {
    'simple': format_simple,
    'json': format_json,
}


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
