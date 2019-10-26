#include <stdio.h>

typedef enum {
    LOL_DEBUG,
    LOL_INFO,
    LOL_WARNING,
    LOL_ERROR,
    LOL_CRITICAL,
} lol_level_t;

typedef struct lol_logger_t {
    char *name;
    lol_level_t level;
    FILE *fh;

    void (*debug)(struct lol_logger_t *self, ...);
    void (*info)(struct lol_logger_t *self, ...);

} lol_logger_t;

lol_logger_t *
lol_make_logger(char *name);

void
lol_free_logger(lol_logger_t *logger);
