#pragma once
#include <Arduino.h>

namespace LCDManager {
  void begin();
  void showStatus(const String& l1, const String& l2);       // idle screen
  void showMessage(const String& title, const String& body); // priority, auto-expires
  bool isShowingMessage();
  void maintain();   // call every loop - handles scrolling & expiry
}
