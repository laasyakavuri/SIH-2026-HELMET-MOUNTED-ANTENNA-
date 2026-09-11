# Main ESP32 firmware — Smart Helmet

## Board
ESP32 Dev Module. Arduino core: "esp32 by Espressif Systems" (Boards Manager).

## Required Arduino libraries (Library Manager)
- Firebase Arduino Client Library for ESP8266 and ESP32 — by Mobizt
- LiquidCrystal I2C — by Frank de Brabander / Marco Schwartz

## Wiring
| Signal | ESP32 |
|---|---|
| LCD VCC | 5V (VIN) |
| LCD GND | GND |
| LCD SDA | GPIO 21 |
| LCD SCL | GPIO 22 |
| Buzzer + | GPIO 25 (− to GND) |
| SOS button | GPIO 26 to GND (internal pull-up) |

No GPS module is used — location comes from phone GPS via Firebase.

## Configuration (config.h)
- WIFI_SSID / WIFI_PASSWORD (2.4 GHz only)
- FIREBASE_DATABASE_URL (ends with "/") + FIREBASE_API_KEY (legacy Database Secret)
- HELMET_ID: HELMET_01..04 to match the Ground Station

## Arduino IDE steps
1. Preferences -> Additional Board URLs:
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
2. Boards Manager -> install esp32. Board: ESP32 Dev Module.
3. Library Manager -> install the two libraries above.
4. Open helmet-esp32.ino, edit config.h.
5. Select COM port -> Upload (hold BOOT if needed).
6. Serial Monitor: 115200 baud.

## Expected serial output
[WIFI] connected - IP: ... -> [FB] begin done -> [FB] message stream started
Button press prints [SOS] and pushes to alerts/. GS messages beep + scroll on LCD.

## Status
Software verified. Hardware physically untested — verify wiring on your bench.
