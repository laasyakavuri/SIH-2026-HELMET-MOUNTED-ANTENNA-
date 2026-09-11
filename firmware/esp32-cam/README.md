# AI-Thinker ESP32-CAM firmware

## Board
AI-Thinker ESP32-CAM (OV2640). Board package: esp32 by Espressif Systems.
Board selection: AI Thinker ESP32-CAM. No extra libraries needed.

## Programming (no USB on board) — 5V FTDI
| FTDI | ESP32-CAM |
|---|---|
| 5V  | 5V |
| GND | GND |
| TX  | U0R |
| RX  | U0T |

Flash: connect GPIO 0 to GND, press RST, upload, remove jumper, press RST.

## Configuration (config.h)
CAM_WIFI_SSID / CAM_WIFI_PASS (2.4 GHz only).

## Verify
1. Serial Monitor at 115200 baud prints:
   ESP32-CAM ready / IP address: 192.168.x.x / Stream: http://192.168.x.x:80/stream
2. Open http://<ESP32-CAM-IP>/stream in a browser.
3. Put the URL in ground-station .env: VITE_CAMERA_HELMET_01_URL=http://<ip>/stream

## Notes
- Power from 5V >= 2A supply; brownout disabled in firmware.
- GPIO 4 = flash LED (held LOW). Limit stream to 1-2 clients.
- Status: software verified, hardware physically untested.
