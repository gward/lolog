
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#include "lolog.h"

/* private internals */

/**
 * Emit a log message with no attempt at formatting or escaping or anything.
 * It's not machine-readable! This is only suitable for debugging and
 * human consumption.
 */
static void
_simple_log(lolog_t *self, level_t level, va_list argp) {
    if (level < self->level) {
        return;
    }

    char *key, *value;
    char before[] = "\x0\x0";

    while (true) {
        key = va_arg(argp, char *);
        if (!key) {
            fputc('\n', self->fh);
            fflush(self->fh);
            return;
        }
        value = va_arg(argp, char *);
        fprintf(self->fh, "%s%s=%s", before, key, value);
        before[0] = ' ';
    }
}

static void
_simple_debug(lolog_t *self, ...) {
    va_list argp;

    va_start(argp, self);
    _simple_log(self, DEBUG, argp);
    va_end(argp);
}

static void
_simple_info(lolog_t *self, ...) {
    va_list argp;

    va_start(argp, self);
    _simple_log(self, INFO, argp);
    va_end(argp);
}

/* public interface */

lolog_t *
make_logger(char *name) {
    lolog_t *logger = malloc(sizeof(lolog_t));
    logger->name = name;
    logger->level = DEBUG;
    logger->fh = stdout;
    logger->debug = _simple_debug;
    logger->info = _simple_info;
    return logger;
}

void
free_logger(lolog_t *logger) {
    free(logger);
}
