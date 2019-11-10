import ctypes

lolog = ctypes.cdll.LoadLibrary("./liblolog.so")
libc = ctypes.cdll.LoadLibrary("libc.so.6")
libc.stdout


def make_config(default_level: int):
    return lolog.lol_make_config(default_level, libc.stdout)


def make_logger(name: str):
    return lolog.lol_make_logger(name.encode("ascii"))


