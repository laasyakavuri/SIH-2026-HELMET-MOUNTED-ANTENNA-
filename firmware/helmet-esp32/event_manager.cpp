#include "event_manager.h"
#include "firebase_service.h"

namespace {
  struct Ev { String type; String msg; };
  const int N = 8;
  Ev buf[N];
  int head = 0, tail = 0;
  unsigned long lastFlush = 0;
}

void EventManager::begin() {}

void EventManager::push(const String& type, const String& msg) {
  int next = (head + 1) % N;
  if (next == tail) return;  // full - drop
  buf[head] = { type, msg };
  head = next;
}

void EventManager::maintain() {
  if (tail == head) return;
  if (millis() - lastFlush < 1500) return;   // rate-limit DB writes
  if (!FirebaseService::isReady()) return;
  lastFlush = millis();
  FirebaseService::pushEvent(buf[tail].type, buf[tail].msg);
  tail = (tail + 1) % N;
}
