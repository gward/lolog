
try:
    raise ImportError("C version disabled for now")
    from .clolog import (
        make_config,
        make_logger,
    )
except (ImportError, OSError) as err:
    print(err)
    print("fallback to Python implementation")
    from .pylolog import (
        Level,
        init,
        make_config,
        make_logger,
        get_config,
        get_logger,
    )

NOTSET = Level.NOTSET
DEBUG = Level.DEBUG
INFO = Level.INFO
WARNING = Level.WARNING
ERROR = Level.ERROR
CRITICAL = Level.CRITICAL
SILENT = Level.SILENT

__all__ = [
    'Level',
    'init',
    'make_config',
    'make_logger',
    'get_config',
    'get_logger',
]
