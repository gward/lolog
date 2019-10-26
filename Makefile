libsrc = $(wildcard src/*.c)
gensrc = src/gen/simple-loggers.c
libhdr = src/lolog.h

CFLAGS = -g -O0 -Wall -std=c99

default: test

src/gen/simple-loggers.c: src/gen-loggers.py
	mkdir -p $(dir $@)
	./src/gen-loggers.py simple $@

test: test.c $(libsrc) $(gensrc) $(libhdr)
	$(CC) $(CFLAGS) -Isrc -o $@ $< $(libsrc)
