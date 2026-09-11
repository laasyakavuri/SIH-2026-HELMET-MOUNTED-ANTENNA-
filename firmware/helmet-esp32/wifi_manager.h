#pragma once
#include <Arduino.h>

namespace WiFiManager {
  void connect(const char* ssid, const char* pass);
  bool isConnected();
  void maintain();      // call every loop - auto-reconnects
  String ip();
  int rssi();
}
