#include "lib.h"
#include "types.h"
#include <stdio.h>
#include <stdlib.h>

#define ON  1
#define OFF 0

int state = OFF;

// This executes every 10 ms and does the following actions:
// 1. read input variables
// 2. perform a transition if needed
// 3. write output variables according the current state
void light_tick_10ms()
{
  boolean switch_value = read_switch();
  int old_state = state;
  switch(state) {
  case OFF:
    if (switch_value) {
      state = ON;
    }
    break;
  case ON:
    if (! switch_value) {
      state = OFF;
    }
    break;
  default:
    printf("Error. This should never happen");
    exit(-1);
  }

  if (state != old_state) {
    printf("Notify light about to be called\n");
    notify_light(state);
  }
  
  // blah, blah
}
