#include <lolog.h>

int main(int argc, char* argv[]) {
    lol_logger_t *logger = lol_make_logger("myapp");
    logger->level = LOL_INFO;
    logger->info(logger,
                 "key1", "value blah blah o'ding \"dong\"",
                 "key2", "value2",
                 "key3", "value3",
                 NULL);
    logger->debug(logger,
                  "arg", "suppressed by level",
                  NULL);
    lol_free_logger(logger);
}
