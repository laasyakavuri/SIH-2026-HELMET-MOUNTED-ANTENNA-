# Architecture (as implemented)

## Data plane — Firebase Realtime Database
Firebase is the single real-time data layer. Every producer/consumer talks
through six top-level paths: helmets/ locations/ messages/ alerts/ cameras/
events/ (schema in firebase-schema.md).

## Ground Station (React + TS + Vite)
- services/dataService.ts defines the DataService interface; the app wires
  exactly one implementation at boot:
  - RealDataService — live Firebase listeners (onValue/onChildAdded) and
    writes (push/update/set). Used when Firebase env vars exist.
  - MockDataService — full in-browser simulation (movement ticker, alerts,
    message replies). Used in DEMO mode. UI never shows mock data as real.
- hooks/useStation.ts owns state, connection status and toast notifications.
- location/ implements the LocationProvider abstraction:
  MockLocationProvider (simulated walk) and PhoneLocationProvider
  (navigator.geolocation -> Firebase -> map). No GPS hardware exists.

## Firmware
- helmet-esp32 — Wi-Fi manager, Firebase service (streaming messages/{id}
  to LCD+buzzer; pushes alerts/events/heartbeat), 16x2 LCD manager
  (scrolling for >16 chars), non-blocking buzzer patterns, debounced SOS
  button, event queue.
- esp32-cam — AI-Thinker pin map, esp32-camera init, WebServer with /,
  /status, /capture, /stream (MJPEG multipart).

## Alert flow (implemented)
Button press -> debounce -> Firebase alerts push -> GS onChildAdded ->
alert panel + toast -> operator ACKNOWLEDGE -> Firebase update -> persisted.

## Message flow (implemented)
GS input -> messages/{helmetId} push -> ESP32 stream callback -> LCD
(scroll) + buzzer. Mock mode mirrors this locally with labelled [MOCK] replies.
