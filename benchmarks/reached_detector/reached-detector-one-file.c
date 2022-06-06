#ifndef REACHED_DETECTOR_H_
#define REACHED_DETECTOR_H_
#include <sys/types.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

void reached(int bug_number){
	printf("reached ");
	printf("%d\n", bug_number);
	int fd = open("/home/dominic/project/targets/bugs.txt", O_RDWR, S_IRUSR | S_IWUSR);
	struct stat sb;

	if (fstat(fd,&sb) == -1)
	{
		perror("couldn't get file size.\n");
	}

	char *file = mmap(NULL, sb.st_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

	for (int i=0; i < sb.st_size; i++)
	{
		if (file[i]!=',')
		{
			continue;
		}
		int j=0;
		for(; file[i+j+1] >= '0' && file[i+j+1] <= '9'; j++){
		}

		char current_bug_number_array[j];
		for(int k=j; k>0; k--)
		{
			current_bug_number_array[k-1]=file[i+k];
		}
		int current_bug_number = atoi(current_bug_number_array);

		if (current_bug_number == bug_number)
		{
			file[i+j+2] = '1';
		}
	}
	munmap(file, sb.st_size);
	close(fd);
}

#endif