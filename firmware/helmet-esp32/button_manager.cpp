#include "button_manager.h"
#include <Arduino.h>
#include "config.h"

namespace {
  bool lastStable = HIGH;
  bool lastRead = HIGH;
  unsigned long lastChange = 0;
}

void Button::begin() {
  pinMode(PIN_SOS_BTN, BTN_ACTIVE_LOW ? INPUT_PULLUP : INPUT);
  lastStable = digitalRead(PIN_SOS_BTN);
  lastRead = lastStable;
}

bool Button::pressed() {
  bool r = digitalRead(PIN_SOS_BTN);
  unsigned long now = millis();
  if (r != lastRead) {
    lastRead = r;
    lastChange = now;
  }
  if (now - lastChange > SOS_DEBOUNCE_MS && r != lastStable) {
    lastStable = r;
    bool active = BTN_ACTIVE_LOW ? (r == LOW) : (r == HIGH);
    if (active) return true;
  }
  return false;
}
