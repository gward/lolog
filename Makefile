libsrc = $(wildcard src/*.c)
libhdr = src/lolog.h

CFLAGS = -g -O0 -Wall -std=c99

test: test.c $(libsrc) $(libhdr)
	$(CC) $(CFLAGS) -Isrc -o $@ $< $(libsrc)
