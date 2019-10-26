# lolog: low-overhead structured logging library

usage:

    #include <lolog.h>

    void myfunc() {
        lolog_t *logger = make_logger("myapp");
        logger->info(logger, key, val, ...);

        free_logger(logger);
    }

See `test.c` for a working example.

