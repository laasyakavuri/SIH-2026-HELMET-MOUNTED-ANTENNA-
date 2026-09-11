#pragma once
#include <Arduino.h>

namespace Button {
  void begin();
  bool pressed();  // true exactly once per physical press (debounced)
}
