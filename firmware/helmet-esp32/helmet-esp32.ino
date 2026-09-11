/*
 * SIH 2026 — Smart Helmet · Main ESP32 firmware
 * SOS button -> Firebase -> Ground Station
 * Firebase message -> LCD (16x2, auto-scroll) + buzzer
 */
#include <Arduino.h>
#include <Wire.h>

#include "config.h"
#include "wifi_manager.h"
#include "firebase_service.h"
#include "lcd_manager.h"
#include "buzzer_manager.h"
#include "button_manager.h"
#include "event_manager.h"

static unsigned long lastStatusRefresh = 0;

static String shortId() {
  String s = HELMET_ID;
  s.replace("HELMET_", "H");
  return s;
}

void setup() {
  Serial.begin(115200);
  delay(200);

  Wire.begin(LCD_SDA, LCD_SCL);
  LCDManager::begin();
  Buzzer::begin();
  Button::begin();
  EventManager::begin();

  LCDManager::showStatus("SMART HELMET", "booting...");
  Serial.println();
  Serial.println("[HELMET] booting");

  WiFiManager::connect(WIFI_SSID, WIFI_PASSWORD);

  if (WiFiManager::isConnected()) {
    LCDManager::showStatus("WIFI OK", WiFiManager::ip());
    FirebaseService::begin();
    FirebaseService::setOnline(true);
    EventManager::push("helmet_online", String(HELMET_ID) + " powered on");
    Buzzer::beep(2, 80, 100);
  } else {
    LCDManager::showStatus("WIFI FAIL", "check creds");
  }
}

void loop() {
  WiFiManager::maintain();
  FirebaseService::maintain();
  Buzzer::maintain();
  LCDManager::maintain();
  EventManager::maintain();

  // retry Firebase until ready
  if (WiFiManager::isConnected() && !FirebaseService::isReady()) {
    static unsigned long lastRetry = 0;
    if (millis() - lastRetry > 15000) {
      lastRetry = millis();
      FirebaseService::begin();
    }
  }

  // physical SOS button
  if (Button::pressed()) {
    Serial.println("[SOS] button pressed");
    Buzzer::beep(3, 120, 120);
    LCDManager::showMessage("SOS!", "sending to GS..");
    bool ok = FirebaseService::sendSos();
    if (ok) {
      EventManager::push("sos_triggered", String(HELMET_ID) + " SOS button pressed");
      LCDManager::showMessage("SOS", "SENT to station");
    } else {
      LCDManager::showMessage("SOS", "SEND FAILED");
    }
    delay(300);  // brief lockout
  }

  // Ground Station messages -> LCD + buzzer
  String msg;
  if (FirebaseService::popMessage(msg)) {
    Serial.println("[MSG] " + msg);
    Buzzer::beep(2, 100, 100);
    LCDManager::showMessage("GS MESSAGE", msg);
    EventManager::push("message_received", "Displayed GS message on LCD");
  }

  // idle status screen refresh
  if (millis() - lastStatusRefresh > 5000) {
    lastStatusRefresh = millis();
    if (!LCDManager::isShowingMessage()) {
      String l1 = shortId() + " " + (WiFiManager::isConnected() ? "ONLINE" : "OFFLINE");
      String l2 = WiFiManager::isConnected() ? WiFiManager::ip() : String("no wifi");
      LCDManager::showStatus(l1, l2);
    }
  }
}
