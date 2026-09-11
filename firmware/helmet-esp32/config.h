#pragma once
// SIH Smart Helmet - main ESP32 configuration
// EDIT LOCALLY. Never commit real credentials.

// Wi-Fi (2.4 GHz only)
#define WIFI_SSID     "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Firebase Realtime Database
// API key here = legacy Database Secret (Project settings -> Service accounts
// -> Database secrets). URL must end with '/'.
#define FIREBASE_API_KEY      "YOUR_FIREBASE_DATABASE_SECRET"
#define FIREBASE_DATABASE_URL "https://YOUR_FIREBASE_PROJECT_ID-default-rtdb.firebaseio.com/"

// Identity
#define HELMET_ID   "HELMET_01"
#define HELMET_NAME "Helmet 01"

// Pins
#define LCD_I2C_ADDR 0x27      // try 0x3F if the display stays blank
#define LCD_SDA      21
#define LCD_SCL      22
#define PIN_BUZZER   25        // buzzer (+), other leg to GND
#define PIN_SOS_BTN  26        // button to GND (INPUT_PULLUP)
#define BTN_ACTIVE_LOW 1
#define SOS_DEBOUNCE_MS 50

// Optional battery sense (divider on GPIO34). 0 = disabled.
#define BATTERY_ENABLED 0
#define PIN_BATTERY     34
#define BATTERY_DIVIDER 2.0f
#define BATTERY_MAX_V   4.2f

// Behaviour
#define LCD_COLS 16
#define LCD_ROWS 2
#define MSG_DISPLAY_MS 8000

// Firebase paths (auto-namespaced per helmet)
#define FIREBASE_PATH_HELMET   "helmets/" HELMET_ID
#define FIREBASE_PATH_MESSAGES "messages/" HELMET_ID
#define FIREBASE_PATH_ALERTS   "alerts"
#define FIREBASE_PATH_EVENTS   "events"
