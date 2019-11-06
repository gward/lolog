#!/usr/bin/python3

"""Generate a family of logger functions: _{format}_debug(),
_{format}_info(), etc.

The generated source file does not compile on its own! It must
be #include'd by lolog.c at the right place.
"""

import sys

TEMPLATE = """
static void
{format}_{level_name}(lol_logger_t *self, char *message, ...) {{
    va_list argp;

    va_start(argp, message);
    {format}_log(self, {level_const}, message, argp);
    va_end(argp);
}}
"""

def main():
    format = sys.argv[1]
    outfile = sys.argv[2]
    with open(outfile, "w") as outfile:
        outfile.write("/* generated -- do not edit */\n")
        for level in ["debug", "info", "warning", "error", "critical"]:
            outfile.write(TEMPLATE.format(
                format=format,
                level_name=level,
                level_const="LOL_" + level.upper(),
            ))

main()
