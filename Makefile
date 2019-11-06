libsrc = $(wildcard src/*.c)
libobj = $(subst .c,.o,$(libsrc))
gensrc = src/gen/simple-loggers.c
libhdr = src/lolog.h

CFLAGS = -g -O0 -Wall -std=c99 -fPIC

default: test

src/gen/simple-loggers.c: src/gen-loggers.py
	mkdir -p $(dir $@)
	./src/gen-loggers.py simple $@

src/lolog.o: src/gen/simple-loggers.c src/lolog.h

liblolog.so: $(libobj)
	$(CC) $(LDFLAGS) -shared -fPIC -o $@ $(libobj)

test: test.c liblolog.so
	$(CC) $(CFLAGS) -Isrc -Wl,-rpath=$$PWD -o $@ $< liblolog.so
