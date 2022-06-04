#include <stdio.h>
#include <reached-detector.c>

const int HELLO = 1;

int main()
{
  char name[50];
  int marks, i, num;

  reached(1);
  printf("Enter number of students: ");
  scanf("%d", &num);

  FILE *fptr;
  fptr = (fopen("C:\\student.txt", "w"));
  if (fptr == NULL)
  {
    printf("Error!");
    exit(1);
  }
  else if (i == 2)
  {
    printf("elif!");
  }
  else
  {
    printf("else!");
  }

  {
    int testing = 7;
    printf("%d", testing);
  }

  for (i = 0; i < num; ++i)
  {
    printf("For student%d\nEnter name: ", i + 1);
    scanf("%s", name);

    printf("Enter marks: ");
    scanf("%d", &marks);

    fprintf(fptr, "\nName: %s \nMarks=%d \n", name, marks);
  }

  fclose(fptr);
  return 0;
}
