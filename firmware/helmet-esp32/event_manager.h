#pragma once
#include <Arduino.h>

namespace EventManager {
  void begin();
  void push(const String& type, const String& msg); // queued, flushed to Firebase
  void maintain();                                   // call every loop
}
