
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#include "lolog.h"

/* private internals -- lol_config_t */

static void
_config_set_level(lol_config_t *self, char *name, lol_level_t level) {
    lol_level_config_t *level_config = malloc(sizeof(lol_level_config_t));
    level_config->name = name;
    level_config->level = level;
    level_config->next = self->level_configs;
    self->level_configs = level_config;
}


/* private internals -- lol_logger_t */

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

lol_config_t *
lol_make_config(lol_level_t default_level, FILE *fh) {
    lol_config_t *config = malloc(sizeof(lol_config_t));
    config->default_level = default_level;
    config->fh = fh;
    config->level_configs = NULL;
    config->set_level = _config_set_level;
    return config;
}

void
lol_free_config(lol_config_t *config) {
    free(config);
}

lol_logger_t *
lol_make_logger(char *name) {
    lol_logger_t *logger = malloc(sizeof(lol_logger_t));
    logger->name = name;
    logger->level = LOL_NOTSET;
    logger->fh = stdout;
    logger->debug = _simple_debug;
    logger->info = _simple_info;
    return logger;
}

void
lol_free_logger(lol_logger_t *logger) {
    free(logger);
}
