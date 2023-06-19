import io
import json
from typing import Any, List, Tuple

import freezegun
import pytest

import lolog
from lolog import pylolog


def test_init_defaults():
    pylolog.Config._instance = None       # start with a fresh slate

    # the first call to init() succeeds
    cfg = lolog.init()

    # and sets up sensible defaults
    assert cfg.default_level == lolog.DEBUG
    assert cfg.pipeline[0] is pylolog.format_simple
    assert cfg.pipeline[1] is pylolog.output_stream

    # second call is rejected
    with pytest.raises(RuntimeError) as ctx:
        lolog.init()
    assert str(ctx.value).startswith('lolog has already been initialized')


def test_init_custom():
    pylolog.Config._instance = None       # start with a fresh slate

    outfile = io.StringIO()
    cfg = lolog.init(stream=outfile, level=lolog.WARNING)
    assert cfg.default_level == lolog.WARNING


# this test must run with TZ=UTC so that timestamps in log output match
# expectations
@freezegun.freeze_time('2020-01-14T13:14:43', auto_tick_seconds=0.4)
def test_simple_logging():
    outfile = io.StringIO()
    cfg = lolog.make_config()
    cfg.configure(stream=outfile)

    log_foo = cfg.get_logger('foo')
    log_bar = cfg.get_logger('bar')

    log_foo.debug('message 1', name='ted', age=43)
    log_foo.info('message 2', request_id='34a9')
    log_bar.warning('something is wrong', user='joe', smell='fishy')
    log_bar.error('request failed', url='http://localhost/', status=503)
    log_bar.critical('world ending', recommended_action='logout')

    text = outfile.getvalue().splitlines()
    assert len(text) == 5
    assert text[0] == (
        '2020-01-14T13:14:43.000000 message 1 '
        'name=foo level=DEBUG name=ted age=43')
    assert text[1] == (
        '2020-01-14T13:14:43.400000 message 2 '
        'name=foo level=INFO request_id=34a9')
    assert text[2] == (
        '2020-01-14T13:14:43.800000 something is wrong '
        'name=bar level=WARNING user=joe smell=fishy')
    assert text[3] == (
        '2020-01-14T13:14:44.200000 request failed '
        'name=bar level=ERROR url=http://localhost/ status=503')
    assert text[4] == (
        '2020-01-14T13:14:44.600000 world ending '
        'name=bar level=CRITICAL recommended_action=logout')


@freezegun.freeze_time('2020-01-14T13:14:43', auto_tick_seconds=0.4)
def test_fancy_logging():
    outfile = io.StringIO()
    cfg = lolog.make_config()
    cfg.configure(stream=outfile)

    # silence the library (be more strict with lib.guts.deep)
    cfg.set_logger_level('lib.guts', lolog.INFO)
    cfg.set_logger_level('lib.guts.deep', lolog.SILENT)

    applog = cfg.get_logger('myapp')
    liblog = cfg.get_logger('lib.guts')

    assert cfg.get_logger('myapp') is applog
    assert cfg.get_logger('lib.guts') is liblog
    assert cfg.get_logger_level('myapp') == lolog.DEBUG

    liblog.debug('this is a really chatty library', arg1='bla', arg2='hi')
    applog.debug('hello from the app')

    liblog.info('stupid library blathering away',
                a='meep', b='beep', c='ping')
    applog.add_value('request_id', '244a')
    applog.info('useful info from the app')

    subliblog = lolog.get_logger('lib.guts.deep')
    assert subliblog is not liblog
    subliblog.debug('this sublib is also noisy', arg='!!!')
    subliblog.error('even its error messages are too noisy')

    text = outfile.getvalue().splitlines()
    assert len(text) == 3

    assert text[0] == (
        '2020-01-14T13:14:43.000000 hello from the app '
        'name=myapp level=DEBUG')
    assert text[1] == (
        '2020-01-14T13:14:43.400000 stupid library blathering away '
        'name=lib.guts level=INFO a=meep b=beep c=ping')
    assert text[2] == (
        '2020-01-14T13:14:43.800000 useful info from the app '
        'name=myapp level=INFO request_id=244a')


class Dummy:
    def __str__(self):
        return 'dummy object'


def test_format_json():
    config = lolog.make_config()
    ts = 1581411252.431693

    # first time with empty log map -- no extra fields
    logmap: List[Tuple[str, Any]] = []
    rec = pylolog.Record(
        ts, 'foo', lolog.DEBUG, 'hello "world"', logmap, outbuf=[])

    outrec = pylolog.format_json(config, rec)
    assert outrec is rec
    assert json.loads(''.join(outrec.outbuf)) == {
        'time': '2020-02-11T08:54:12.431693',
        'name': 'foo',
        'level': 'DEBUG',
        'message': 'hello "world"',
    }

    def gen():
        yield 3
        yield 'b'

    # now with some more interesting stuff in logmap
    logmap = [
        ('c1', 'simple string'),
        ('c2', '←‽→'),
        ('c3', {'foo': 42}),
        ('c4', gen()),
        ('c5', Dummy()),
    ]
    rec = pylolog.Record(
        ts, 'merp.bla', lolog.ERROR, 'hello "world"', logmap, outbuf=[])

    outrec = pylolog.format_json(config, rec)
    assert outrec is not None
    assert json.loads(''.join(outrec.outbuf)) == {
        'time': '2020-02-11T08:54:12.431693',
        'name': 'merp.bla',
        'level': 'ERROR',
        'message': 'hello "world"',
        'c1': 'simple string',
        'c2': '←‽→',
        'c3': {'foo': 42},
        'c4': [3, 'b'],
        'c5': 'dummy object',
    }


@freezegun.freeze_time('2020-01-14T16:00:00', auto_tick_seconds=0.1)
def test_replace():
    outfile = io.StringIO()
    cfg = lolog.make_config()
    cfg.configure(stream=outfile)
    ts = 1581411252.431693

    rec1 = pylolog.Record(
        ts, 'beep.bop', lolog.INFO, 'test msg', [], outbuf=[])
    rec2 = rec1.replace()
    assert rec1 == rec2

    rec3 = rec1.replace(level=lolog.DEBUG, message='ding')
    assert rec3 != rec1
    assert rec3.level is lolog.DEBUG
    assert rec3.message == 'ding'

    def replace_stage(config, record):
        if record.name == 'foo':
            record = record.replace(message='HELLO ' + record.message)
        return record

    cfg.insert_stage(0, replace_stage)

    log_foo = cfg.get_logger('foo')
    log_bar = cfg.get_logger('bar')

    log_foo.info('test 1')
    log_bar.debug('test 2')

    lines = outfile.getvalue().splitlines()
    assert lines[0] == '2020-01-14T16:00:00.000000 HELLO test 1 name=foo level=INFO'
    assert lines[1] == '2020-01-14T16:00:00.100000 test 2 name=bar level=DEBUG'
