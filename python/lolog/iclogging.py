"""intercept calls to the standard logging module"""

import logging
from typing import Type

from .pylolog import Config, Level


class Interceptor:
    def __init__(self, cfg: Config, logger_cls: Type):
        self.cfg = cfg
        self.logger_cls = logger_cls
        self.save = {}

    def intercept(self):
        for level in [
                Level.DEBUG,
                Level.INFO,
                Level.WARNING,
                Level.ERROR,
                Level.CRITICAL,
        ]:
            name = level.name
            lower_name = name.lower()
            locals = {'cfg': self.cfg, 'Level': level}
            func_text = """
def {lower_name}(self, msg, *args, **kwargs):
    items = [("arg%d" % (i + 1), arg) for (i, arg) in enumerate(args)]
    items += kwargs.items()
    cfg.get_logger(self.name)._log(Level.{name}, msg, items)
""".format(name=name, lower_name=lower_name)

            exec(func_text, locals, locals)
            self.save[lower_name] = getattr(logging.Logger, lower_name)
            setattr(logging.Logger, lower_name, locals[lower_name])

    def undo(self):
        for (name, method) in self.save.items():
            setattr(logging.Logger, name, method)
        self.save.clear()
