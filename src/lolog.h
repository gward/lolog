#include <stdio.h>

typedef enum {
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
} level_t;

typedef struct lolog_t {
    char *name;
    level_t level;
    FILE *fh;

    void (*debug)(struct lolog_t *self, ...);
    void (*info)(struct lolog_t *self, ...);

} lolog_t;

lolog_t *
make_logger(char *name);

void
free_logger(lolog_t *logger);
