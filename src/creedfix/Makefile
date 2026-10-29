# Builds dinput.dll (creedfix) with MinGW-w64 (i686).
CC      = i686-w64-mingw32-gcc
CFLAGS  = -m32 -O2 -masm=intel -Wall -Wextra -Wno-unused-parameter -fno-asynchronous-unwind-tables
LDFLAGS = -shared -static-libgcc -s -Wl,--kill-at -Wl,--enable-stdcall-fixup

dinput.dll: creedfix.c
	$(CC) $(CFLAGS) -o $@ creedfix.c $(LDFLAGS)

clean:
	rm -f dinput.dll
