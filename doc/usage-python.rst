Usage (Python)
==============

Concepts and data types
-----------------------

Config
++++++

lolog defines a small number of types which interact to produce log output.
The starting point is ``Config``,
which is where all log configuration lives.
Normally there will be exactly one instance of ``Config`` per process,
but you are free to create more if you like.
(This might be useful in test code.)
Most other lolog objects reference a ``Config`` object.

You can configure logging and get a ``Config`` object in one shot::

    cfg = lolog.init()

This creates and returns
the global default ``Config`` object.
When called with no arguments,
``init()`` configures reasonable defaults
for logging in development:

  * emit all log messages (default level is ``DEBUG``)
  * write log messages to stderr
  * format in simple human-readable plain text: ``key=val ...``

You can override each of these
with optional keyword arguments:
see the API reference for details.

You are only allowed to call ``init()`` once per process.
(Library code MUST NOT call ``init()`` —
it is reserved for application startup code.)
See below for other ways to get a ``Config`` object.

All configuration information lives in the config object:

  * The default log level, used by loggers with no explicit log level.
  * The log level for each logger (if configured).
  * The pipeline, a list of functions that operate on log records.

The default pipeline created by ``init()`` looks like:

       formatter  →  stream output

Pipelines will be described in more detail below.

Logger
++++++

Your interactions with ``Config``
should mostly happen at application initialization time.
The vast majority of time that you use lolog,
you will be working with ``Logger`` objects directly.
Every logger is named and tied to a config object.
The usual way to get a logger is from the global default config::

    log = lolog.get_logger('foo.bar')

But if you are working with a custom config,
you can fetch a logger from it::

    log = cfg.get_logger('foo.bar')

Logger names can be any string,
but I recommend a
dot-separated sequence of short ASCII tokens.
Further, logger names should describe the code
responsible for the messages emitted
by that logger.
In Python, this is easily done
by using the fully-qualified module name::

    log = lolog.get_logger(__name__)

For example, if this is in file ``foo/bar.py`` (module ``foo.bar``),
messages will be emitted by the logger named ``foo.bar``.

lolog has no concept of a relationship between loggers:
it has no idea that logger ``foo`` and ``foo.bar``
come from related code.
That is, the configuration for ``foo``
has no affect on any other logger,
not even ``foo.bar``.

If you want to affect the behaviour of many loggers,
use a pattern::

    cfg.set_logger_pattern_level('foo.*', lolog.INFO)

Levels and level filtering
++++++++++++++++++++++++++

Log level describes the importance of a log message.
This lets you filter out less important messages
and focus on the important stuff,
at least in your production environment.
In development, you probably want to see everything
(or at least everything from your own code).
lolog's levels enable all of this.

Log levels are defined by the ``Level`` enum.
The sequence of log levels,
from least important to most important, is:

  * ``DEBUG``
  * ``INFO``
  * ``WARNING``
  * ``ERROR``
  * ``CRITICAL``

There are two other values in the ``Level`` enum:

  * ``NOTSET``: used to detect when the desired log level
    has not been configured
  * ``SILENT``: used to completely suppress all log output

These can both be used in configuration,
but not used as the level of a log message.

Whenever a log message is emitted,
it has a level.
The level is determined by the method called:
``log.debug`` emits messages with level ``DEBUG``, etc.
The message level is compared to the level
configured for that logger,
or to the config's default level
if the logger has not been configured.
If the message level is *less than* the configured level,
this message is dropped.

For example, if lolog's default config object
has been configured like::

    cfg.set_default_level(lolog.INFO)
    cfg.set_logger_level("foo", lolog.DEBUG)
    cfg.set_logger_level("bar", lolog.WARNING)
    cfg.set_logger_level("noo", lolog.SILENT)

Then the following messages will be emitted::

    lolog.get_logger("foo").debug("kept")
    lolog.get_logger("foo").info("kept")
    lolog.get_logger("bar").warning("kept")
    lolog.get_logger("qux").info("kept")

but these will be suppressed::

    lolog.get_logger("bar").info("dropped")
    lolog.get_logger("qux").debug("dropped")
    lolog.get_logger("noo").critical("nuclear launch detected")

Record
++++++

Every log message results in a ``Record`` object.
If all you do is call methods on a logger
and read log files,
this is normally invisible to you.

But if you need to customize lolog
by writing new pipeline stages,
you will have to interact with ``Record`` objects.

Every log record has the following attributes:

  * ``time``: float, seconds since POSIX epoch
  * ``name``: str, name of the logger that created this record
  * ``level``: Level, determined by the logger method called
  * ``message``: str, the fixed string passed as the first argument
  * ``context``: list of key-value pairs
  * ``outbuf``: used for interaction between format and output stages

The logging pipeline
--------------------

Every ``Config`` object has exactly one pipeline,
which is a sequence of pipeline *stages*.
Each stage is a callable with signature::

    stage(config: Config, record: Record) -> Optional[Record]

where

  * ``config`` is the config object that is in charge
  * ``record`` contains all the information available
    at the time the log message was created

To drop this log record, return None.
Otherwise, return the log record
(possibly modified).

Each pipeline stage must additionally have a couple of attributes:

  * ``mut``: bool, does the stage mutate the log record?
  * ``fmt``: bool, does the stage format the log record?
  * ``out``: bool, does the stage output the log record?

There are various ways to satisfy these requirements,
but the easiest is to use
lolog's ``stage()`` decorator.

Filtering stage
+++++++++++++++

For example, here is a custom filtering stage
that drops INFO-level messages
from noisylib
that contain the string ``"foobar"``::

    import lolog

    @lolog.stage()
    def filter(config: lolog.Config, record: lolog.Record) -> Optional[lolog.Record]:
        if (record.name == "noisylib"
              and record.level == lolog.INFO
              and "foobar" in record.message):
            return None
        return record

The ``@stage()`` decorator sets all required attributes, 
defaulting to False.

Mutating stage
++++++++++++++

Imagine instead that you don't want to drop those ``"foobar"`` messages from noisylib,
just censor out the dangerous word ``"foobar"``.
You can do that with a mutating pipeline stage::

    @lolog.stage(mut=True)
    def mutate(config: lolog.Config, record: lolog.Record) -> Optional[lolog.Record]:
        if (record.name == "noisylib"
              and record.level == lolog.INFO
              and "foobar" in record.message):
            record.message = record.message.replace("foobar", "******")
        return record

Be careful not to fall off the end
of a stage function and implicitly return None!
That will drop the log message,
probably not your intention.
