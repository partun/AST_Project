#ifndef REACHED_DETECTOR_H_
#define REACHED_DETECTOR_H_

#include <sys/types.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

void reached(int bug_number);

#endif
