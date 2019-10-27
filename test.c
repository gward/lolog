#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define __USE_POSIX
#include <time.h>
#include <sys/time.h>

#include <lolog.h>

static int
timefunc(char *buf, size_t size) {
    const char *fmt = "%FT%T";
    const int tslen = 19 + 7;       /* yyyy-mm-ddThh:mm:ss.uuuuuu */

    if (size < tslen + 1) {
        return 0;
    }

    struct timeval now_tv;
    if (gettimeofday(&now_tv, NULL) < 0) {
        return 0;
    }

    int nbytes = 0;
    struct tm now_tm;
    localtime_r(&now_tv.tv_sec, &now_tm);
    nbytes += strftime(buf, size - 7, fmt, &now_tm);
    assert(now_tv.tv_usec < 1000000);
    nbytes += snprintf(buf + 19, 7 + 1, ".%06ld", now_tv.tv_usec);
    return nbytes;
}

int main(int argc, char* argv[]) {
    lol_config_t *config = lol_make_config(LOL_DEBUG, stdout);
    config->set_level(config, "myapp", LOL_INFO);
    config->set_level(config, "lib", LOL_SILENT);

    lol_logger_t *applog = lol_make_logger("myapp");
    lol_logger_t *liblog = lol_make_logger("lib");

    applog->add_dynamic_context(applog, "ts", timefunc);
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
    liblog->critical(liblog, "this logger really cries wolf a lot", NULL);
    lol_free_logger(applog);
    lol_free_logger(liblog);
    lol_free_config(config);
}
