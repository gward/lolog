"""intercept calls to the standard logging module"""

import threading

from .pylolog import Config, Level


class InterceptManager:
    """replacement for logging.Manager class"""

    def __init__(self, cfg):
        self.mutex = threading.Lock()
        self.cfg = cfg
        self.logger = {}

    def getLogger(self, name):
        with self.mutex:
            if name not in self.logger:
                self.logger[name] = InterceptLogger(self.cfg, name)
            return self.logger[name]


class InterceptLogger:
    """replacement for logging.Logger class"""
    def __init__(self, cfg, name):
        self.logger = cfg.get_logger(name)

    def debug(self, msg, *args, **kwargs):
        self._log(Level.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(Level.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(Level.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(Level.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(Level.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        pass                    # ummm...

    def _log(self, level, msg, *args, **kwargs):
        items = [("arg%d" % (i + 1), arg)
                 for (i, arg) in enumerate(args)]
        items += kwargs.items()
        self.logger._log(level, msg, items)


_save_manager = None
_save_root = None


def intercept(cfg: Config):
    global _save_manager, _save_root
    import logging

    _save_manager = logging.Logger.manager
    _save_root = logging.Logger.root

    manager = InterceptManager(cfg)
    logging.Logger.manager = manager
    logging.Logger.root = manager.getLogger("")


def undo_intercept():
    global _save_manager, _save_root
    import logging

    logging.Logger.manager = _save_manager
    logging.Logger.root = _save_root
    _save_manager = _save_root = None
