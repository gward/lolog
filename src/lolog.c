
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lolog.h"

/* private internals -- lol_config_t */

static lol_config_t *default_config = NULL;

static void
_config_set_level(lol_config_t *self, char *name, lol_level_t level) {
    lol_logger_config_t *logger_config = malloc(sizeof(lol_logger_config_t));
    logger_config->name = name;
    logger_config->level = level;
    logger_config->next = self->logger_configs;
    self->logger_configs = logger_config;
}

static lol_config_t *
_get_config() {
    if (!default_config) {
        fprintf(stderr,
                "lolog: cannot configure logger: "
                "no default configuration set\n");
        abort();
    }
    return default_config;
}


/* private internals -- lol_logger_t */

static void
_configure_logger(lol_logger_t *self) {
    lol_config_t *config = _get_config();
    lol_logger_config_t *logger_config;
    for (logger_config = config->logger_configs;
         logger_config != NULL;
         logger_config = logger_config->next) {
        if (strcmp(logger_config->name, self->name) == 0) {
            self->level = logger_config->level;
            break;
        }
    }
}


/**
 * Emit a log message with no attempt at formatting or escaping or anything.
 * It's not machine-readable! This is only suitable for debugging and
 * human consumption.
 */
static void
_simple_log(lol_logger_t *self, lol_level_t level, va_list argp) {
    if (self->level == LOL_NOTSET) {
        _configure_logger(self);
    }

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

#include "gen/simple-loggers.c"

/* public interface */

lol_config_t *
lol_make_config(lol_level_t default_level, FILE *fh) {
    lol_config_t *config = malloc(sizeof(lol_config_t));
    config->default_level = default_level;
    config->fh = fh;
    config->logger_configs = NULL;
    config->set_level = _config_set_level;
    default_config = config;
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
    logger->warning = _simple_warning;
    logger->error = _simple_error;
    logger->critical = _simple_critical;
    return logger;
}

void
lol_free_logger(lol_logger_t *logger) {
    free(logger);
}
