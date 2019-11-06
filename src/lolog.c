#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "lolog.h"

/* private internals -- shared across types */

static void
free_context(lol_context_t *context) {
    lol_context_t *next;
    for (; context != NULL; context = next) {
        next = context->next;
        free(context);
    }
}

/**
 * Append new context record to the end of a context list
 * (order matters!)
 */
static void
append_context(lol_context_t **head,
               char *key,
               char *value,
               char *(*valuefunc)()) {
    lol_context_t *context = malloc(sizeof(lol_context_t));
    context->key = key;
    context->value = value;
    context->valuefunc = valuefunc;
    context->next = NULL;

    lol_context_t *tail;
    for (tail = *head; tail && tail->next; tail = tail->next) {
    }
    if (!tail) {
        *head = context;
    } else {
        tail->next = context;
    }
}


/* private internals -- lol_config_t */

static lol_config_t *default_config = NULL;

static void
config_set_level(lol_config_t *self, char *name, lol_level_t level) {
    lol_logger_config_t *logger_config = malloc(sizeof(lol_logger_config_t));
    logger_config->name = name;
    logger_config->level = level;
    logger_config->next = self->logger_configs;
    self->logger_configs = logger_config;
}

static void
config_add_static_context(lol_config_t *self,
                          char *key,
                          char *value) {
    append_context(&self->context, key, value, NULL);
}

static void
config_add_dynamic_context(lol_config_t *self,
                           char *key,
                           char *(*valuefunc)()) {
    append_context(&self->context, key, NULL, valuefunc);
}

static lol_config_t *
get_config() {
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
configure_logger(lol_logger_t *self) {
    lol_config_t *config = get_config();
    self->config = config;
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

static void
add_item(item_t *items,
         int *item_idx,
         char *key,
         char *value,
         bool alloced) {
    items[*item_idx].key = key;
    items[*item_idx].value = value;
    items[*item_idx].alloced = alloced;
    (*item_idx)++;
}

static void
add_context_items(item_t *items,
                  int *item_idx,
                  lol_context_t *context) {
    for (; context; context = context->next) {
        if (context->valuefunc) {
            add_item(items,
                     item_idx,
                     context->key,
                     context->valuefunc(),
                     true);
        } else {
            add_item(items,
                     item_idx,
                     context->key,
                     context->value,
                     false);
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
    add_context_items(items, &item_idx, self->config->context);
    add_context_items(items, &item_idx, self->context);

    // add the message
    add_item(items, &item_idx, "message", message, false);

    // and finish with the items for this line
    char *key, *value;
    while (true) {
        key = va_arg(argp, char *);
        if (!key) {
            break;
        }
        value = va_arg(argp, char *);
        add_item(items, &item_idx, key, value, false);
    }

    return item_idx;            /* number of items */
}

static void
simple_format(item_t *items, int num_items, char *buf, size_t max_output) {
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
simple_log(lol_logger_t *self,
           lol_level_t level,
           char *message,
           va_list argp) {
    if (self->level == LOL_NOTSET) {
        configure_logger(self);
    }

    if (level < self->level) {
        return;
    }

    item_t items[MAX_ITEMS];
    int num_items = build_items(self, items, message, argp);

    char buf[MAX_OUTPUT];
    simple_format(items, num_items, buf, MAX_OUTPUT);

    fputs(buf, self->fh);
    fflush(self->fh);
}

#include "gen/simple-loggers.c"

static void
logger_add_static_context(lol_logger_t *self,
                          char *key,
                          char *value) {
    append_context(&self->context, key, value, NULL);
}

static void
logger_add_dynamic_context(lol_logger_t *self,
                           char *key,
                           char *(*valuefunc)()) {
    append_context(&self->context, key, NULL, valuefunc);
}

/* public interface */

lol_config_t *
lol_make_config(lol_level_t default_level, FILE *fh) {
    lol_config_t *config = malloc(sizeof(lol_config_t));
    config->default_level = default_level;
    config->context = NULL;
    config->fh = fh;
    config->logger_configs = NULL;
    config->set_level = config_set_level;
    config->add_context = config_add_static_context;
    config->add_dynamic_context = config_add_dynamic_context;
    default_config = config;
    return config;
}

void
lol_free_config(lol_config_t *config) {
    free_context(config->context);

    lol_logger_config_t *lconfig, *next;
    for (lconfig = config->logger_configs; lconfig != NULL; lconfig = next) {
        next = lconfig->next;
        free(lconfig);
    }

    free(config);
}

lol_logger_t *
lol_make_logger(char *name) {
    lol_logger_t *logger = malloc(sizeof(lol_logger_t));
    logger->name = name;
    logger->level = LOL_NOTSET;
    logger->fh = stdout;
    logger->context = NULL;
    logger->debug = simple_debug;
    logger->info = simple_info;
    logger->warning = simple_warning;
    logger->error = simple_error;
    logger->critical = simple_critical;
    logger->add_context = logger_add_static_context;
    logger->add_dynamic_context = logger_add_dynamic_context;
    return logger;
}

void
lol_free_logger(lol_logger_t *logger) {
    free_context(logger->context);
    free(logger);
}
