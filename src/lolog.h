#include <stdio.h>

typedef enum {
    LOL_NOTSET,                 /* indicates an unconfigured logger */
    LOL_DEBUG,
    LOL_INFO,
    LOL_WARNING,
    LOL_ERROR,
    LOL_CRITICAL,
    LOL_SILENT,                 /* no logs ever emitted at this level */
} lol_level_t;

typedef struct lol_logger_config_t {
    char *name;
    lol_level_t level;
    struct lol_logger_config_t *next;
} lol_logger_config_t;

typedef struct lol_config_t {
    lol_level_t default_level;
    FILE *fh;
    lol_logger_config_t *logger_configs;

    void (*set_level)(struct lol_config_t *self, char *name, lol_level_t level);
} lol_config_t;

typedef struct lol_logger_t {
    char *name;
    lol_level_t level;
    FILE *fh;

    void (*debug)(struct lol_logger_t *self, ...);
    void (*info)(struct lol_logger_t *self, ...);

} lol_logger_t;

lol_config_t *
lol_make_config(lol_level_t default_level, FILE *fh);

void
lol_free_config(lol_config_t *config);

lol_logger_t *
lol_make_logger(char *name);

void
lol_free_logger(lol_logger_t *logger);
