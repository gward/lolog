
try:
    from .clolog import make_config, make_logger
except (ImportError, OSError) as err:
    print(err)
    print("fallback to Python implementation")
    from .pylolog import (
        Level,
        get_config,
        get_logger,
        make_config,
        make_logger,
        isotime,
    )
