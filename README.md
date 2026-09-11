# SIH 2026 — Smart Helmet Command & Control System

A working prototype: 4 smart helmets monitored from a dark command/control
Ground Station, with Firebase Realtime Database as the real-time data layer,
main-ESP32 firmware (LCD/buzzer/SOS button), and AI-Thinker ESP32-CAM firmware
(MJPEG CCTV). Location comes from PHONE GPS (never a NEO-6M GPS module).

## Architecture
GPS module -> LocationProvider -> FIREBASE -> GROUND STATION LIVE MAP
AI-THINKER ESP32-CAM -> Wi-Fi HTTP/MJPEG -> GROUND STATION CCTV
MAIN ESP32 (SOS button / LCD / buzzer) <-> FIREBASE <-> GROUND STATION
ESP32 SOS -> FIREBASE -> GROUND STATION ALERT

## Repository structure
- ground-station/   React + TypeScript + Vite dashboard (REAL + DEMO/MOCK mode)
- firmware/helmet-esp32/   main ESP32 Arduino firmware
- firmware/esp32-cam/      AI-Thinker ESP32-CAM MJPEG firmware
- firebase/         rules + setup docs
- docs/             architecture, schema, hardware, demo-mode, troubleshooting

## Ground Station setup (works instantly in DEMO mode)
    cd ground-station
    npm install
    npm run dev        -> open http://localhost:5173

No Firebase credentials, no hardware needed — the dashboard boots in
DEMO (MOCK) mode with 4 simulated helmets, moving GPS, mock cameras,
SOS alerts, messaging, timeline and notifications.

## Production build
    npm run build
    npm run preview

## Firebase setup (REAL mode)
1. console.firebase.google.com -> create project -> add Realtime Database.
2. Copy firebase/.env.example -> ground-station/.env and fill the values.
3. Paste the rules from firebase/database.rules.json (DEV ONLY — open rules).
4. Restart npm run dev — header shows MODE: REAL + FIREBASE: LIVE.

## ESP32 / ESP32-CAM setup
See firmware/helmet-esp32/README.md and firmware/esp32-cam/README.md
(wiring, libraries, Arduino IDE steps). The CAM prints
"Stream: http://<ip>/stream" — put it in VITE_CAMERA_HELMET_0X_URL.

## REAL / MOCK / FUTURE
| Feature | Class | Status |
|---|---|---|
| Firebase RTDB sync | REAL | Implemented (needs credentials) |
| ESP32 LCD/buzzer/SOS via Firebase | REAL | Implemented (hardware-untested) |
| ESP32-CAM MJPEG /stream | REAL | Implemented (hardware-untested) |
| Simulated GPS/helmets/cameras/alerts | MOCK | Working |
| Phone GPS (browser geolocation) | REAL | Implemented via LocationProvider |
| Production auth / hosting | FUTURE | Not in prototype |

## Packaging ZIPs
    python bootstrap_sih.py
Creates sih-smart-helmet-complete.zip, ground-station.zip, firmware.zip.
