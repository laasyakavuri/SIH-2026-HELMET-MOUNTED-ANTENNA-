#pragma once
#include <Arduino.h>

namespace Buzzer {
  void begin();
  void beep(int times, int onMs, int offMs); // non-blocking pattern
  void maintain();                           // call every loop
}
