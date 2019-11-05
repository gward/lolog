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

#define MAX_ITEMS 64

// includes terminating nul character
#define MAX_OUTPUT 4096

typedef struct {
    char *key;
    char *value;
    bool alloced;
} item_t;

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

static int
build_items(lol_logger_t *self,
            item_t *items,
            char *message,
            va_list argp) {
    // build list of items (key/value pairs), starting with context
    int item_idx = 0;
    lol_context_t *context;
    for (context = self->context; context; context = context->next) {
        item_t *item = items + item_idx;
        item->key = context->key;
        if (context->valuefunc) {
            item->value = context->valuefunc();
            item->alloced = true;
        } else {
            item->value = context->value;
            item->alloced = false;
        }
        item_idx++;
    }

    // add the message
    items[item_idx].key = "message";
    items[item_idx].value = message;
    items[item_idx].alloced = false;
    item_idx++;

    // and finish with the items for this line
    char *key, *value;
    while (true) {
        key = va_arg(argp, char *);
        if (!key) {
            break;
        }
        value = va_arg(argp, char *);
        items[item_idx].key = key;
        items[item_idx].value = value;
        items[item_idx].alloced = false;
        item_idx++;
    }

    return item_idx;            /* number of items */
}

static void
_simple_format(item_t *items, int num_items, char *buf, size_t max_output) {
    // max_output - 1 to leave room for the newline
    size_t remaining = max_output - 1;

    // format all items into the output buffer, and then write it
    bool truncated = false;
    int offset = 0;
    for (int item_idx = 0; item_idx < num_items; item_idx++) {
        item_t item = items[item_idx];
        size_t key_len = strlen(item.key);
        size_t value_len = strlen(item.value);
        int needed = key_len + 1 + value_len + 1;
        if (!truncated && needed > remaining) {
            truncated = true;   /* print warning? */
        }

        if (!truncated) {
            strncpy(buf + offset,
                    item.key,
                    remaining);
            buf[offset + key_len] = '=';
            offset += key_len + 1;
            remaining -= key_len + 1;

            strncpy(buf + offset,
                    item.value,
                    remaining);
            bool is_last = (item_idx == num_items - 1);
            buf[offset + value_len] = is_last ? '\n' : ' ';
            offset += value_len + 1;
            remaining -= value_len + 1;
            buf[offset] = 0;
        }

        if (item.alloced) {
            free(item.value);
        }
    }
}

/**
 * Emit a log message with no attempt at formatting or escaping or anything.
 * It's not machine-readable! This is only suitable for debugging and
 * human consumption.
 */
static void
_simple_log(lol_logger_t *self,
            lol_level_t level,
            char *message,
            va_list argp) {
    if (self->level == LOL_NOTSET) {
        _configure_logger(self);
    }

    if (level < self->level) {
        return;
    }

    item_t items[MAX_ITEMS];
    int num_items = build_items(self, items, message, argp);

    char buf[MAX_OUTPUT];
    _simple_format(items, num_items, buf, MAX_OUTPUT);

    fputs(buf, self->fh);
    fflush(self->fh);
}

#include "gen/simple-loggers.c"

/**
 * Append new context record to the end of self->context list
 * (order matters!)
 */
static void
_append_context(lol_logger_t *self, lol_context_t *context) {
    lol_context_t *tail;
    for (tail = self->context; tail && tail->next; tail = tail->next) {
    }
    if (!tail) {
        self->context = context;
    } else {
        tail->next = context;
    }
}

static void
_add_static_context(lol_logger_t *self, char *key, char *value) {
    lol_context_t *context = malloc(sizeof(lol_context_t));
    context->key = key;
    context->value = value;
    context->valuefunc = NULL;
    context->next = NULL;

    _append_context(self, context);
}

static void
_add_dynamic_context(lol_logger_t *self, char *key, char *(*valuefunc)()) {
    lol_context_t *context = malloc(sizeof(lol_context_t));
    context->key = key;
    context->value = NULL;
    context->valuefunc = valuefunc;
    context->next = NULL;

    _append_context(self, context);
}

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
    logger->context = NULL;
    logger->debug = _simple_debug;
    logger->info = _simple_info;
    logger->warning = _simple_warning;
    logger->error = _simple_error;
    logger->critical = _simple_critical;
    logger->add_context = _add_static_context;
    logger->add_dynamic_context = _add_dynamic_context;
    return logger;
}

void
lol_free_logger(lol_logger_t *logger) {
    free(logger);
}
