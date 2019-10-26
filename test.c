#include <lolog.h>

int main(int argc, char* argv[]) {
    lolog_t *logger = make_logger("myapp");
    logger->level = INFO;
    logger->info(logger,
                 "key1", "value blah blah o'ding \"dong\"",
                 "key2", "value2",
                 "key3", "value3",
                 NULL);
    logger->debug(logger,
                  "arg", "suppressed by level",
                  NULL);
    free_logger(logger);
}
