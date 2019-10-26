#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define __USE_POSIX
#include <time.h>
#include <sys/time.h>

#include <lolog.h>

static char *
timefunc() {
    // XXX EVIL: this leaks memory on every log message ... but free()
    // is not the answer, since we should write into a buffer rather
    // than dynamically allocate bits of the log message
    char *buf = calloc(sizeof(char), 40);
    struct timeval now_tv;
    if (gettimeofday(&now_tv, NULL) < 0) {
        return NULL;
    }

    const int tslen = 19;       /* yyyy-mm-ddThh:mm:ss */
    struct tm now_tm;
    localtime_r(&now_tv.tv_sec, &now_tm);
    strftime(buf, 40, "%FT%T", &now_tm);
    sprintf(buf + tslen, ".%06ld", now_tv.tv_usec);
    return buf;
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
