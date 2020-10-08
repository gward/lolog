import io

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
    assert cfg.pipeline[0] is pylolog.filter_level
    assert cfg.pipeline[1] is pylolog.format_simple
    assert cfg.pipeline[1].fmt
    assert cfg.pipeline[2] is pylolog.output_stream
    assert cfg.pipeline[2].out

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

    log_foo.debug('message 1', name='ted', age=43)
    log_foo.info('message 2', request_id='34a9')

    text = outfile.getvalue().splitlines()
    assert len(text) == 2
    assert text[0] == (
        'time=2020-01-14T13:14:43.000000 name=foo level=DEBUG '
        'message=message 1 name=ted age=43')
    assert text[1] == (
        'time=2020-01-14T13:14:43.400000 name=foo level=INFO '
        'message=message 2 request_id=34a9')
