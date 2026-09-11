#include "buzzer_manager.h"
#include <Arduino.h>
#include "config.h"

namespace {
  const int FREQ = 2400;
  bool beeping = false;
  int remain = 0;
  bool toneOn = false;
  unsigned long nextFlip = 0;
  int onMs = 100, offMs = 100;

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  inline void toneStart() { ledcWriteTone(PIN_BUZZER, FREQ); }
  inline void toneStop()  { ledcWriteTone(PIN_BUZZER, 0); }
#else
  inline void toneStart() { ledcWriteTone(0, FREQ); }
  inline void toneStop()  { ledcWriteTone(0, 0); }
#endif
}

void Buzzer::begin() {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_BUZZER, FREQ, 8);   // core 3.x API
#else
  ledcSetup(0, FREQ, 8);             // core 2.x API
  ledcAttachPin(PIN_BUZZER, 0);
#endif
  toneStop();
}

void Buzzer::beep(int times, int onMs_, int offMs_) {
  remain = times * 2;   // on + off per beep
  onMs = onMs_;
  offMs = offMs_;
  beeping = true;
  toneOn = false;
  nextFlip = 0;
}

void Buzzer::maintain() {
  if (!beeping) return;
  unsigned long now = millis();
  if (nextFlip == 0) nextFlip = now;
  if (now < nextFlip) return;

  if (toneOn) {
    toneStop();
    toneOn = false;
    remain--;
    nextFlip = now + offMs;
  } else if (remain > 0) {
    toneStart();
    toneOn = true;
    nextFlip = now + onMs;
  } else {
    beeping = false;
  }
}
