# lolog: low-overhead structured logging library

lolog is a library for simple, low-overhead, structured logging in Python and C. The goals of the project are:

  * Structured logging: each log message is a fixed string accompanied by a bunch of key/value pairs. This makes large-scale log analysis easier.
  * Keep it simple and debuggable: I never want to spend another hour of my life trying to figure out why some expected log output is not seen, or why it's being duplicated, or formatted weirdly.
  * Minimize overhead: I don't want you to worry about the runtime cost of keeping a `log.debug(...)` call in your code. The impact of filtering it out in production should be very low.
  * Be flexible in the ways that you need, without unnecessary complexity.

## Basics

Basic usage in Python is

    import sys, os
    import lolog

    log = lolog.get_logger("main")

    def main():
        lolog.init(level=lolog.INFO, format="simple", stream=sys.stdout)
        log.add_context("pid", os.getpid())
        log.info("starting up", prog=sys.argv[0])
        log.debug("detailed debug info", foo=42, thing="blah")

    main()

The output of this program will be something like

    time=2020-09-27T11:53:50.552246 name=main level=INFO message=starting up pid=6954 prog=readme-test.py

`lolog.init()` only lets you tweak three settings:

  * Global log level. In this case, all messages at level DEBUG (which is lower than INFO) are filtered out.
  * Log format: in real life, you will most likely want `format="json"`.
  * Output file: you can send your log messages anywhere you like, as long as it's a writeable file-like object. Anything fancier than that will require work by you.

Behind the scenes, lolog uses a pipeline to process log messages. In this case, `init()` creates a two-stage pipeline:

  * A _formatter_ to combine all the inputs into a single string: in this case, it's the human-friendly (but not machine-friendly!) `time=... name=...`.
  * An _output stage_ to write that string to a file.

## Filtering by log level

Filtering on a global log level is usually too coarse. In real life, maybe you want to keep INFO and up by default, DEBUG and up for your own code, but only WARNING and up for a library that annoys you by logging too much information at level INFO. Not a problem:

    lolog.init(level=lolog.INFO, format="simple", stream=sys.stdout)
    lolog.set_logger_level("myapp", lolog.DEBUG)
    lolog.set_logger_level("noisylib", lolog.WARNING)

With this setup, if your code looks like

    log = lolog.get_logger("myapp")

    log.info("something interesting")
    log.debug("not as interesting")

then both of those messages will be emitted. But if noisylib does this:

    log = lolog.get_logger("noisylib")

    log.info("low-level debug info that nobody cares about")
    log.warning("something important happened")

then only the warning message will be emitted.

## Formatting

lolog's builtin `simple` format is way too simple. It's easy for humans to read, which is why it's the default. But when your code is deployed, you almost certainly want JSON logs for machine readability. That's easy:

    lolog.init(level=lolog.INFO, format="json", stream=sys.stdout)

If you have invented a brilliant new markup language that is destined to replace JSON, you'll have to write your own formatter.

## Context

The key to structured logging is that list of key-value pairs included with every log message. But what's lurking unseen is the log _context_, which is just a bunch of additional key-value pairs that are automatically added to the log message.

In fact, lolog has several levels of context: global, thread-local, and logger. Global context lives in the `Config` object, and that's where you put things like the process ID. Thread-local context also lives in the `Config` object, but is used for values that vary by thread: current request ID, current username, current client IP address, etc. Finally, logger context exists in each logger object. Its use is limited only by your imagination.

## Output

lolog's builtin facilities output are its least flexible feature. In Python, you can write logs to any writeable file-like object: period. In C, you can write logs to any stdio stream: period.

If your runtime environment requires that applications themselves write to log files, or rotate log files, or send log events to syslog or off-host: 2003 called, it wants its logging policy back. You really need to reconsider your logging environment. In the meantime, you'll have to write your own output stage.

## Fancy stuff

lolog's pipeline is a very general mechanism. As mentioned above, you can write custom formatters or output stages to handle cases that lolog doesn't handle.

But say you want to drop DEBUG messages from noisylib on Tuesdays, unless they contain the string "foobar", you can do that. You just have to write a custom filter stage and insert it into the pipeline.

Or maybe you want to mutate messages: every INFO message from noisylib that contains the string "foobar" should be downgraded to DEBUG, and then subject to usual filtering policy. Again: write a custom stage and insert it into the pipeline.

All of these are outside the scope of a README file. See the main documentation for details.

## Contributing to lolog

See [HACKING.md](HACKING.md).
