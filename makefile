all: Source/daemonize.c Source/daemonize.h Source/main.c
	gcc Source/daemonize.c Source/main.c -lrt -lpthread -o NanoHatOLED
