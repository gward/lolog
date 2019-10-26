# lolog: low-overhead structured logging library

usage:

    #include <lolog.h>

    void myfunc() {
        lol_logger_t *logger = lol_make_logger("myapp");
        logger->info(logger, key, val, ...);

        lol_free_logger(logger);
    }

See `test.c` for a working example.

