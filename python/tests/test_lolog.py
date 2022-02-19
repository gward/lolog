import io
import json

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
    assert cfg.pipeline[0].fmt
    assert cfg.pipeline[1] is pylolog.output_stream
    assert cfg.pipeline[1].out

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
        'time=2020-01-14T13:14:43.000000 name=foo level=DEBUG '
        'message=message 1 name=ted age=43')
    assert text[1] == (
        'time=2020-01-14T13:14:43.400000 name=foo level=INFO '
        'message=message 2 request_id=34a9')
    assert text[2] == (
        'time=2020-01-14T13:14:43.800000 name=bar level=WARNING '
        'message=something is wrong user=joe smell=fishy')
    assert text[3] == (
        'time=2020-01-14T13:14:44.200000 name=bar level=ERROR '
        'message=request failed url=http://localhost/ status=503')
    assert text[4] == (
        'time=2020-01-14T13:14:44.600000 name=bar level=CRITICAL '
        'message=world ending recommended_action=logout')


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
    applog.add_context('request_id', '244a')
    applog.info('useful info from the app')

    subliblog = lolog.get_logger('lib.guts.deep')
    assert subliblog is not liblog
    subliblog.debug('this sublib is also noisy', arg='!!!')
    subliblog.error('even its error messages are too noisy')

    text = outfile.getvalue().splitlines()
    assert len(text) == 3

    assert text[0] == (
        'time=2020-01-14T13:14:43.000000 name=myapp level=DEBUG '
        'message=hello from the app')
    assert text[1] == (
        'time=2020-01-14T13:14:43.400000 name=lib.guts level=INFO '
        'message=stupid library blathering away '
        'a=meep b=beep c=ping')
    assert text[2] == (
        'time=2020-01-14T13:14:43.800000 name=myapp level=INFO '
        'message=useful info from the app request_id=244a')


class Dummy:
    def __str__(self):
        return 'dummy object'


def test_format_json():
    config = lolog.make_config()
    ts = 1581411252.431693

    # first time with empty context -- no extra fields
    context = []
    rec = pylolog.Record(
        ts, 'foo', lolog.DEBUG, 'hello "world"', context, outbuf=[])

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

    # now with some more interesting stuff in context
    context = [
        ('c1', 'simple string'),
        ('c2', '←‽→'),
        ('c3', {'foo': 42}),
        ('c4', gen()),
        ('c5', Dummy()),
    ]
    rec = pylolog.Record(
        ts, 'merp.bla', lolog.ERROR, 'hello "world"', context, outbuf=[])

    outrec = pylolog.format_json(config, rec)
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
