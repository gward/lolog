
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
_simple_log(lol_logger_t *self, lol_level_t level, va_list argp) {
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
_simple_debug(lol_logger_t *self, ...) {
    va_list argp;

    va_start(argp, self);
    _simple_log(self, LOL_DEBUG, argp);
    va_end(argp);
}

static void
_simple_info(lol_logger_t *self, ...) {
    va_list argp;

    va_start(argp, self);
    _simple_log(self, LOL_INFO, argp);
    va_end(argp);
}

/* public interface */

lol_logger_t *
lol_make_logger(char *name) {
    lol_logger_t *logger = malloc(sizeof(lol_logger_t));
    logger->name = name;
    logger->level = LOL_DEBUG;
    logger->fh = stdout;
    logger->debug = _simple_debug;
    logger->info = _simple_info;
    return logger;
}

void
lol_free_logger(lol_logger_t *logger) {
    free(logger);
}
