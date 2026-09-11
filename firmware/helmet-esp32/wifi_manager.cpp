#include "wifi_manager.h"
#include <WiFi.h>

namespace {
  unsigned long lastAttempt = 0;
}

void WiFiManager::connect(const char* ssid, const char* pass) {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid, pass);
  Serial.printf("[WIFI] connecting to %s", ssid);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(400);
    Serial.print('.');
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[WIFI] connected - IP: %s - RSSI: %d\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
  } else {
    Serial.println("[WIFI] not connected yet (will keep retrying)");
  }
  lastAttempt = millis();
}

bool WiFiManager::isConnected() { return WiFi.status() == WL_CONNECTED; }

void WiFiManager::maintain() {
  if (!isConnected() && millis() - lastAttempt > 10000) {
    lastAttempt = millis();
    Serial.println("[WIFI] reconnecting...");
    WiFi.disconnect();
    WiFi.reconnect();
  }
}

String WiFiManager::ip() { return WiFi.localIP().toString(); }
int WiFiManager::rssi() { return WiFi.RSSI(); }
