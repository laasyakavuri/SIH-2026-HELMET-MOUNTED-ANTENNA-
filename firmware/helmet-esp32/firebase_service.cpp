#include "firebase_service.h"

#include <WiFi.h>
#include <time.h>
#include <Firebase_ESP_Client.h>

#include "config.h"

namespace {

  FirebaseData fbio;       // writes
  FirebaseData fbstream;   // message stream
  FirebaseAuth auth;
  FirebaseConfig cfg;

  bool started = false;
  bool streamUp = false;
  unsigned long lastHeartbeat = 0;
  unsigned long lastStreamAttempt = 0;
  long lastMsgTs = -1;

  const int QSIZE = 4;
  String msgQ[QSIZE];
  int qHead = 0, qTail = 0;

  long epochNow() {
    time_t t = time(nullptr);
    return (t > 1600000000) ? (long)t : 0;
  }

  void enqueueMessage(const String& text) {
    int next = (qHead + 1) % QSIZE;
    if (next == qTail) return;  // full - drop
    msgQ[qHead] = text;
    qHead = next;
  }

  void streamCallback(FirebaseStream data) {
    if (data.dataType() != "json" && data.dataType() != "object") return;
    FirebaseJson json = data.to<FirebaseJson>();
    FirebaseJsonData res;
    long ts = -1;
    String text;
    if (json.get(res, "timestamp")) ts = (long)res.intValue;
    if (json.get(res, "text")) text = res.stringValue;
    if (text.length() == 0) return;
    if (ts >= 0 && ts == lastMsgTs) return;  // duplicate guard
    lastMsgTs = ts;
    enqueueMessage(text);
    Serial.println("[FB] GS message queued");
  }

  void streamTimeout(bool timeout) {
    if (timeout) Serial.println("[FB] stream timeout");
  }

}  // namespace

void FirebaseService::begin() {
  if (started) return;
  if (WiFi.status() != WL_CONNECTED) return;

  cfg.database_url = FIREBASE_DATABASE_URL;
  cfg.signer.tokens.legacy_token = FIREBASE_API_KEY;

  Firebase.begin(&cfg, &auth);
  Firebase.reconnectWiFi(true);

  fbio.setResponseSize(2048);
  fbstream.setBSSLBufferSize(2048, 1024);
  fbstream.setResponseSize(2048);

  configTime(0, 0, "pool.ntp.org");
  started = true;
  Serial.println("[FB] begin done");
}

bool FirebaseService::isReady() {
  return started && Firebase.ready() && WiFi.status() == WL_CONNECTED;
}

void FirebaseService::maintain() {
  if (!started || WiFi.status() != WL_CONNECTED) {
    streamUp = false;
    return;
  }

  if (!streamUp && millis() - lastStreamAttempt > 5000) {
    lastStreamAttempt = millis();
    if (Firebase.beginStream(fbstream, FIREBASE_PATH_MESSAGES)) {
      fbstream.setStreamCallback(streamCallback, streamTimeout);
      streamUp = true;
      Serial.println("[FB] message stream started");
    }
  }

  if (streamUp && !fbstream.httpConnected()) {
    streamUp = false;  // dropped - retry on next window
  }

  if (millis() - lastHeartbeat > 30000) {
    lastHeartbeat = millis();
    FirebaseService::setOnline(true);
  }
}

bool FirebaseService::setOnline(bool online) {
  if (!isReady()) return false;
  FirebaseJson j;
  j.set("id", HELMET_ID);
  j.set("name", HELMET_NAME);
  j.set("status", online ? "online" : "offline");
  long ts = epochNow();
  if (ts > 0) j.set("lastSeen", (int)ts);
#if BATTERY_ENABLED
  int raw = analogRead(PIN_BATTERY);
  float volts = raw * 3.3f / 4095.0f * BATTERY_DIVIDER;
  j.set("battery", (int)(volts / BATTERY_MAX_V * 100.0f));
#endif
  return Firebase.updateNodeAsync(fbio, FIREBASE_PATH_HELMET, j);
}

bool FirebaseService::sendSos() {
  if (!isReady()) return false;
  FirebaseJson j;
  j.set("helmetId", HELMET_ID);
  j.set("type", "SOS");
  long ts = epochNow();
  j.set("timestamp", ts > 0 ? (int)ts : (int)(millis() / 1000));
  j.set("status", "active");
  j.set("acknowledged", false);
  bool ok = Firebase.pushAsync(fbio, FIREBASE_PATH_ALERTS, j);
  Serial.println(ok ? "[FB] SOS pushed" : "[FB] SOS push FAILED");
  return ok;
}

bool FirebaseService::pushEvent(const String& type, const String& message) {
  if (!isReady()) return false;
  FirebaseJson j;
  j.set("helmetId", HELMET_ID);
  j.set("type", type);
  j.set("message", message);
  long ts = epochNow();
  j.set("timestamp", ts > 0 ? (int)ts : (int)(millis() / 1000));
  return Firebase.pushAsync(fbio, FIREBASE_PATH_EVENTS, j);
}

bool FirebaseService::popMessage(String& out) {
  if (qTail == qHead) return false;
  out = msgQ[qTail];
  msgQ[qTail] = "";
  qTail = (qTail + 1) % QSIZE;
  return true;
}
