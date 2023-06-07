#include "types.h"
#include <stdio.h>
#include <stdlib.h>

boolean read_switch()
{
  printf("It just fails because this is just for testing\n");
  exit(-1);
  return 0;
}


void notify_light(boolean b)
{
  printf("Light is now %d\n", b);
}
