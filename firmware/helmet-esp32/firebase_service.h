#pragma once
#include <Arduino.h>

namespace FirebaseService {
  void begin();                       // call after Wi-Fi is up; safe to re-call
  bool isReady();
  void maintain();                    // call every loop: stream + heartbeat
  bool setOnline(bool online);        // helmets/{id} heartbeat
  bool sendSos();                     // push to alerts/
  bool pushEvent(const String& type, const String& message);
  bool popMessage(String& out);       // true when a GS message is queued
}
