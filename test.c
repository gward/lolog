#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define __USE_POSIX
#include <time.h>
#include <sys/time.h>

#include <lolog.h>

static char *
timefunc() {
    // Hmmm: this returns a dynamically allocated string, which the
    // logger frees after output.
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
    config->set_level(config, "lib", LOL_SILENT);
    config->set_level(config, "lib", LOL_INFO);
    config->add_dynamic_context(config, "ts", timefunc);

    lol_logger_t *applog = lol_make_logger("myapp");
    lol_logger_t *liblog = lol_make_logger("lib");

    applog->add_context(applog, "request_id", "a925");

    applog->info(applog,
                 "hello from applog at info level",
                 "arg1", "value blah blah o'ding \"dong\"",
                 "arg2", "value2",
                 NULL);
    liblog->debug(liblog,
                  "this is an annoyingly noisy library",
                  "arg", "bla bla bla",
                  NULL);
    applog->debug(applog,
                  "this is from applog, and should be suppressed",
                  NULL);
    applog->info(applog, "log message with no args is legit", NULL);
    liblog->critical(liblog,
                     "this logger really cries wolf a lot",
                     "blaaaaaaaaah", "wha wha wha wha!",
                     NULL);
    lol_free_logger(applog);
    lol_free_logger(liblog);
    lol_free_config(config);
}
