#include <stdio.h>

#include <lolog.h>

static char *
timefunc() {
    return "about 6 o'clock";
}

int main(int argc, char* argv[]) {
    lol_config_t *config = lol_make_config(LOL_DEBUG, stdout);
    config->set_level(config, "myapp", LOL_INFO);
    config->set_level(config, "myapp", LOL_DEBUG);
    config->set_level(config, "lib", LOL_SILENT);

    lol_logger_t *applog = lol_make_logger("myapp");
    lol_logger_t *liblog = lol_make_logger("lib");

    applog->add_dynamic_context(applog, "ts", timefunc);
    applog->add_context(applog, "request_id", "a925");

    applog->info(applog,
                 "key1", "value blah blah o'ding \"dong\"",
                 "key2", "value2",
                 "key3", "value3",
                 NULL);
    liblog->debug(liblog, "junk", "annoying noisy library", NULL);
    applog->debug(applog,
                  "arg", "suppressed by level",
                  NULL);
    liblog->critical(liblog, "crap", "this logger really cries wolf a lot");
    lol_free_logger(applog);
    lol_free_logger(liblog);
    lol_free_config(config);
}
