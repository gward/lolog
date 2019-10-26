#include <stdio.h>

#include <lolog.h>

int main(int argc, char* argv[]) {
    lol_config_t *config = lol_make_config(LOL_DEBUG, stdout);
    config->set_level(config, "myapp", LOL_INFO);
    config->set_level(config, "lib", LOL_SILENT);

    lol_logger_t *logger = lol_make_logger("myapp");
    lol_logger_t *liblog = lol_make_logger("lib");

    logger->info(logger,
                 "key1", "value blah blah o'ding \"dong\"",
                 "key2", "value2",
                 "key3", "value3",
                 NULL);
    liblog->debug(liblog, "junk", "annoying noisy library", NULL);
    logger->debug(logger,
                  "arg", "suppressed by level",
                  NULL);
    liblog->critical(liblog, "crap", "this logger really cries wolf a lot");
    lol_free_logger(logger);
    lol_free_logger(liblog);
    lol_free_config(config);
}
