import io

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
