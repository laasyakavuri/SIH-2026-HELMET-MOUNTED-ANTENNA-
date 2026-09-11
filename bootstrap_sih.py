#!/usr/bin/env python3
# bootstrap_sih.py — SIH 2026 Smart Helmet: full repo generator + build + ZIP packaging.
# Usage:  python bootstrap_sih.py     (Windows: py bootstrap_sih.py)

import os, sys, shutil, zipfile, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

FILES = {}

# ---------------------------- ROOT ----------------------------
FILES["README.md"] = r'''
# SIH 2026 — Smart Helmet Command & Control System

A working prototype: 4 smart helmets monitored from a dark command/control
Ground Station, with Firebase Realtime Database as the real-time data layer,
main-ESP32 firmware (LCD/buzzer/SOS button), and AI-Thinker ESP32-CAM firmware
(MJPEG CCTV). Location comes from PHONE GPS (never a NEO-6M GPS module).

## Architecture
PHONE GPS -> LocationProvider -> FIREBASE -> GROUND STATION LIVE MAP
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
'''

FILES[".gitignore"] = r'''
node_modules/
dist/
.env
.env.*
!.env.example
*.zip
.DS_Store
*.log
'''

FILES["package-zips.sh"] = r'''
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -f sih-smart-helmet-complete.zip ground-station.zip firmware.zip
find . -name node_modules -type d -prune -exec rm -rf {} + 2>/dev/null || true
zip -rq sih-smart-helmet-complete.zip . -x "*.zip" -x "*/.git/*" -x "bootstrap_sih.py"
zip -rq ground-station.zip ground-station
zip -rq firmware.zip firmware
echo "Created:"
unzip -l sih-smart-helmet-complete.zip | tail -1
unzip -l ground-station.zip | tail -1
unzip -l firmware.zip | tail -1
'''

FILES["package-zips.ps1"] = r'''
 $ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Remove-Item *.zip -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter node_modules |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Get-ChildItem | Where-Object { $_.Name -ne '.git' -and $_.Name -ne 'bootstrap_sih.py' }) -DestinationPath sih-smart-helmet-complete.zip
Compress-Archive -Path ground-station -DestinationPath ground-station.zip
Compress-Archive -Path firmware -DestinationPath firmware.zip
Write-Host "Created: sih-smart-helmet-complete.zip, ground-station.zip, firmware.zip"
'''

# ---------------------------- docs/ ----------------------------
FILES["docs/architecture.md"] = r'''
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
'''

FILES["docs/firebase-schema.md"] = r'''
# Firebase Realtime Database schema

helmets/HELMET_01: { id, name, status: "online"|"offline", lastSeen, battery }
locations/HELMET_01: { helmetId, lat, lng, timestamp }
messages/HELMET_01/<pushId>: { helmetId, direction: "gs_to_helmet"|"helmet_to_gs",
                               text, timestamp, status }
alerts/<pushId>: { helmetId, type: "SOS"|..., timestamp,
                   status: "active"|"acknowledged", acknowledged: bool }
cameras/HELMET_01: { id, helmetId, streamUrl, status: "online"|"offline"|"mock"|"unconfigured" }
events/<pushId>: { helmetId, type: helmet_online|helmet_offline|location_update|
                   sos_triggered|alert_acknowledged|message_sent|message_received|
                   camera_online|camera_offline, message, timestamp }

Rules shipped in firebase/database.rules.json are OPEN — dev/prototype ONLY.
Harden before real deployment:
  { "rules": { ".read": "auth != null", ".write": "auth != null" } }
'''

FILES["docs/hardware.md"] = r'''
# Hardware (as wired in this prototype)

## Main ESP32 (DevKit v1, 30-pin)
| Peripheral | ESP32 pins | Notes |
|---|---|---|
| 1602A LCD + I2C backpack | SDA=21, SCL=22, VCC=5V, GND | addr 0x27 (try 0x3F) |
| Buzzer | GPIO25 (+), GND (-) | NPN transistor for loud passives |
| SOS button | GPIO26 to GND | INPUT_PULLUP, active-LOW, 50 ms debounce |
| Battery sense (optional) | GPIO34 | BATTERY_ENABLED 1 in config.h |

## AI-Thinker ESP32-CAM
On-board OV2640, no external camera wiring. Programming: 5V FTDI
(5V/GND, TX->U0R, RX->U0T), GPIO0 to GND during reset to flash.
GPIO4 = on-board flash LED (held LOW in firmware).

## GPS hardware: NONE
Location = phone GPS -> LocationProvider -> Firebase. NEO-6M is explicitly
NOT part of this system.
'''

FILES["docs/demo-mode.md"] = r'''
# Demo mode (MOCK)

Triggered automatically when Firebase env vars are missing, or forced with
VITE_DEMO_MODE=true. Header shows MODE: MOCK, banner explains it, and every
simulated camera feed is labelled MOCK.

Simulated: 4 helmets with random-walk GPS (2 s tick), battery drain,
online/offline toggles, camera states, SOS alerts, GS-to-helmet messages
with [MOCK] helmet replies, activity timeline, toast notifications.

Demo controls bar (bottom): TRIGGER SOS, TOGGLE ONLINE, TOGGLE CAMERA,
SIMULATE LOCATION, PUSH THIS DEVICE GPS (real browser geolocation via
PhoneLocationProvider, clearly labelled).

Nothing in demo mode claims a physical device, camera, or Firebase link.
'''

FILES["docs/ground-station.md"] = r'''
# Ground Station

Stack: React 18, TypeScript, Vite 5, Leaflet/react-leaflet, Firebase JS SDK.

Layout: header (mode/firebase/online count/clock) - left (fleet list, SOS
panel) - center (live map + 2x2 CCTV grid, click to enlarge) - right
(details, messaging, timeline). Bottom MOCK demo bar in demo mode. Toasts
top-right. Responsive to mobile.

Key modules: services/dataService.ts (interface + REAL/MOCK switch),
firebase/config.ts (env parsing, camera URLs), hooks/useStation.ts,
utils/camera.ts (REAL/MOCK/OFFLINE resolution).
'''

FILES["docs/troubleshooting.md"] = r'''
# Troubleshooting

- Map gray / no tiles — OSM tiles need internet; markers still work offline.
- Blank LCD — wrong I2C address: change LCD_I2C_ADDR 0x27 to 0x3F; check 5V.
- Firebase permission denied — paste rules from firebase/database.rules.json.
- Firebase.ready() never true — DATABASE_URL must end with "/", legacy token
  from Project settings -> Service accounts -> Database secrets.
- ESP32-CAM upload fails — GPIO0 to GND, press RST, correct COM port, 5V supply.
- Camera shows OFFLINE but stream works in browser — set
  VITE_CAMERA_HELMET_0X_URL then restart npm run dev.
- Port busy on upload — close any Serial Monitor.
- Node too old — Vite 5 needs Node 18+; install from nodejs.org.
'''

# ---------------------------- firebase/ ----------------------------
FILES["firebase/.env.example"] = r'''
# Copy values into ground-station/.env
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_DATABASE_URL=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
'''

FILES["firebase/database.rules.json"] = r'''
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
'''

FILES["firebase/README.md"] = r'''
# Firebase setup

1. console.firebase.google.com -> create project.
2. Build -> Realtime Database -> Create database.
3. Rules -> paste database.rules.json contents -> Publish (DEV ONLY, open rules).
4. Project settings -> Web app -> copy the config values.
5. Service accounts -> Database secrets -> copy the legacy secret
   (the ESP32 firmware uses this as FIREBASE_API_KEY).
6. Put values into ground-station/.env.
7. cd ground-station && npm run dev -> header must show MODE: REAL,
   FIREBASE: LIVE.

Never commit .env. The shipped rules are OPEN — prototype only.
'''

# ---------------------- ground-station root ----------------------
FILES["ground-station/package.json"] = r'''
{
  "name": "sih-smart-helmet-ground-station",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "firebase": "^10.12.2",
    "leaflet": "^1.9.4",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-leaflet": "^4.2.1"
  },
  "devDependencies": {
    "@types/leaflet": "^1.9.12",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.3",
    "vite": "^5.4.2"
  }
}
'''

FILES["ground-station/tsconfig.json"] = r'''
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
'''

FILES["ground-station/vite.config.ts"] = r'''
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
});
'''

FILES["ground-station/index.html"] = r'''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SIH Smart Helmet — Ground Control Station</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''

FILES["ground-station/.env.example"] = r'''
# true = force DEMO/MOCK (no Firebase needed). Remove or set false + fill
# the Firebase block below for REAL mode.
VITE_DEMO_MODE=true

VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_DATABASE_URL=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=

# ESP32-CAM MJPEG streams (REAL CCTV). Firmware prints the URL on Serial.
VITE_CAMERA_HELMET_01_URL=
VITE_CAMERA_HELMET_02_URL=
VITE_CAMERA_HELMET_03_URL=
VITE_CAMERA_HELMET_04_URL=
'''

FILES["ground-station/.gitignore"] = r'''
node_modules/
dist/
.env
.env.local
'''

# ---------------------- ground-station src core ----------------------
FILES["ground-station/src/vite-env.d.ts"] = r'''
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DEMO_MODE?: string;
  readonly VITE_FIREBASE_API_KEY?: string;
  readonly VITE_FIREBASE_AUTH_DOMAIN?: string;
  readonly VITE_FIREBASE_DATABASE_URL?: string;
  readonly VITE_FIREBASE_PROJECT_ID?: string;
  readonly VITE_FIREBASE_STORAGE_BUCKET?: string;
  readonly VITE_FIREBASE_MESSAGING_SENDER_ID?: string;
  readonly VITE_FIREBASE_APP_ID?: string;
  readonly VITE_CAMERA_HELMET_01_URL?: string;
  readonly VITE_CAMERA_HELMET_02_URL?: string;
  readonly VITE_CAMERA_HELMET_03_URL?: string;
  readonly VITE_CAMERA_HELMET_04_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
'''

FILES["ground-station/src/main.tsx"] = r'''
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/global.css';

// No StrictMode: services hold live streams/timers that must not double-start.
createRoot(document.getElementById('root')!).render(<App />);
'''

FILES["ground-station/src/App.tsx"] = r'''
import { useState } from 'react';
import { useStation } from './hooks/useStation';
import { HELMET_IDS } from './models/constants';
import Header from './components/Header';
import HelmetList from './components/HelmetList';
import AlertsPanel from './components/AlertsPanel';
import MapPanel from './components/MapPanel';
import CctvGrid from './components/CctvGrid';
import DetailsPanel from './components/DetailsPanel';
import MessagingPanel from './components/MessagingPanel';
import TimelinePanel from './components/TimelinePanel';
import DemoControls from './components/DemoControls';
import Toasts from './components/Toasts';

export default function App() {
  const { state, conn, toasts, service, mode } = useStation();
  const [selectedId, setSelectedId] = useState<string>(HELMET_IDS[0]);
  const onlineCount = HELMET_IDS.filter((id) => state.helmets[id]?.status === 'online').length;

  return (
    <div className="app">
      <Header mode={mode} conn={conn} onlineCount={onlineCount} total={HELMET_IDS.length} />

      {mode === 'MOCK' && (
        <div className="mock-banner">
          DEMO MODE — all helmets, GPS movement, cameras and alerts on this screen are
          <strong> MOCK (simulated)</strong>. Add Firebase credentials in .env for REAL mode.
        </div>
      )}

      <main className="layout">
        <div className="col col-left">
          <HelmetList state={state} selectedId={selectedId} onSelect={setSelectedId} />
          <AlertsPanel
            alerts={state.alerts}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onAck={(id) => service.acknowledgeAlert(id)}
          />
        </div>

        <div className="col col-center">
          <MapPanel state={state} selectedId={selectedId} onSelect={setSelectedId} />
          <CctvGrid state={state} selectedId={selectedId} onSelect={setSelectedId} />
        </div>

        <div className="col col-right">
          <DetailsPanel state={state} helmetId={selectedId} />
          <MessagingPanel
            helmetId={selectedId}
            messages={state.messages[selectedId] ?? []}
            onSend={(t) => service.sendMessage(selectedId, t)}
          />
          <TimelinePanel events={state.events} helmetId={selectedId} />
        </div>
      </main>

      {mode === 'MOCK' && <DemoControls helmetId={selectedId} service={service} />}
      <Toasts toasts={toasts} />
    </div>
  );
}
'''

FILES["ground-station/src/models/types.ts"] = r'''
export type HelmetStatus = 'online' | 'offline';

export interface Helmet {
  id: string;
  name: string;
  status: HelmetStatus;
  lastSeen: number | null;
  battery: number | null;
}

export interface LocationPoint {
  helmetId: string;
  lat: number;
  lng: number;
  timestamp: number;
}

export type MessageDirection = 'gs_to_helmet' | 'helmet_to_gs';
export type MessageStatus = 'sent' | 'delivered' | 'read' | 'failed';

export interface Message {
  id: string;
  helmetId: string;
  direction: MessageDirection;
  text: string;
  timestamp: number;
  status: MessageStatus;
}

export type AlertType = 'SOS' | 'IMPACT' | 'MAN_DOWN' | 'GEOFENCE';

export interface Alert {
  id: string;
  helmetId: string;
  type: AlertType;
  timestamp: number;
  status: 'active' | 'acknowledged';
  acknowledged: boolean;
}

export type CameraStatus = 'online' | 'offline' | 'mock' | 'unconfigured';

export interface Camera {
  id: string;
  helmetId: string;
  streamUrl: string | null;
  status: CameraStatus;
}

export type EventType =
  | 'helmet_online'
  | 'helmet_offline'
  | 'location_update'
  | 'sos_triggered'
  | 'alert_acknowledged'
  | 'message_sent'
  | 'message_received'
  | 'camera_online'
  | 'camera_offline';

export interface TimelineEvent {
  id: string;
  helmetId: string;
  type: EventType;
  message: string;
  timestamp: number;
}
'''

FILES["ground-station/src/models/constants.ts"] = r'''
export const HELMET_IDS = ['HELMET_01', 'HELMET_02', 'HELMET_03', 'HELMET_04'] as const;

export const helmetName = (id: string): string => `Helmet ${id.slice(-2)}`;

export const MAP_CENTER: [number, number] = [28.6139, 77.2090];
'''

FILES["ground-station/src/firebase/config.ts"] = r'''
import { initializeApp, type FirebaseApp } from 'firebase/app';
import { getDatabase, type Database } from 'firebase/database';

const env = import.meta.env;

export const firebaseConfig = {
  apiKey: env.VITE_FIREBASE_API_KEY ?? '',
  authDomain: env.VITE_FIREBASE_AUTH_DOMAIN ?? '',
  databaseURL: env.VITE_FIREBASE_DATABASE_URL ?? '',
  projectId: env.VITE_FIREBASE_PROJECT_ID ?? '',
  storageBucket: env.VITE_FIREBASE_STORAGE_BUCKET ?? '',
  messagingSenderId: env.VITE_FIREBASE_MESSAGING_SENDER_ID ?? '',
  appId: env.VITE_FIREBASE_APP_ID ?? '',
};

const forceDemo = (env.VITE_DEMO_MODE ?? '').toLowerCase() === 'true';

export const firebaseConfigured = Boolean(
  firebaseConfig.apiKey && firebaseConfig.databaseURL && firebaseConfig.projectId,
);

/** REAL mode only when credentials exist AND demo not forced. */
export const isRealMode = firebaseConfigured && !forceDemo;

let app: FirebaseApp | null = null;
let db: Database | null = null;

export function getDb(): Database | null {
  if (!isRealMode) return null;
  if (!app) {
    app = initializeApp(firebaseConfig);
    db = getDatabase(app);
  }
  return db;
}

/** Env-configured ESP32-CAM stream URLs (empty string = not configured). */
export const cameraStreamUrls: Record<string, string> = {
 VITE_CAMERA_HELMET_01_URL: env.VITE_CAMERA_HELMET_01_URL ?? '',
  VITE_CAMERA_HELMET_02_URL: env.VITE_CAMERA_HELMET_02_URL ?? '',
  VITE_CAMERA_HELMET_03_URL: env.VITE_CAMERA_HELMET_03_URL ?? '',
  VITE_CAMERA_HELMET_04_URL: env.VITE_CAMERA_HELMET_04_URL ?? '',
'''

FILES["ground-station/src/services/dataService.ts"] = r'''
import type { Alert, Message, TimelineEvent, Helmet, LocationPoint, Camera } from '../models/types';

export type ConnStatus = 'connecting' | 'connected' | 'offline';

export interface StationState {
  helmets: Record<string, Helmet>;
  locations: Record<string, LocationPoint>;
  cameras: Record<string, Camera>;
  messages: Record<string, Message[]>;
  alerts: Alert[];
  events: TimelineEvent[];
}

export interface DataHandlers {
  onState: (s: StationState) => void;
  onConn: (c: ConnStatus) => void;
  onEvent: (e: TimelineEvent) => void;
  onAlert: (a: Alert) => void;
  onMessage: (m: Message) => void;
}

export interface DataService {
  readonly mode: 'REAL' | 'MOCK';
  start(handlers: DataHandlers): void;
  dispose(): void;

  // two-way actions (work in both modes)
  sendMessage(helmetId: string, text: string): void;
  acknowledgeAlert(alertId: string): void;

  // demo/mock controls (no-ops in REAL mode)
  triggerSos(helmetId: string): void;
  toggleHelmetOnline(helmetId: string): void;
  toggleCamera(helmetId: string): void;
  simulateLocation(helmetId: string): void;

  // external location push (PhoneLocationProvider -> Firebase/mock)
  pushExternalLocation(helmetId: string, lat: number, lng: number): void;
}
'''

FILES["ground-station/src/services/realDataService.ts"] = r'''
import type { Database } from 'firebase/database';
import { limitToLast, onChildAdded, onValue, push, query, ref, set, update } from 'firebase/database';
import { getDb } from '../firebase/config';
import type { ConnStatus, DataHandlers, DataService, StationState } from './dataService';
import type { Alert, Camera, Helmet, LocationPoint, Message, TimelineEvent } from '../models/types';
import { HELMET_IDS } from '../models/constants';
import { uid } from '../utils/format';

/** Live Firebase RTDB implementation of DataService (REAL mode). */
export class RealDataService implements DataService {
  readonly mode = 'REAL' as const;
  private db: Database;
  private handlers: DataHandlers | null = null;
  private unsubs: Array<() => void> = [];
  private state: StationState = { helmets: {}, locations: {}, cameras: {}, messages: {}, alerts: [], events: [] };

  constructor() {
    const db = getDb();
    if (!db) throw new Error('RealDataService requires Firebase env configuration');
    this.db = db;
  }

  start(handlers: DataHandlers): void {
    this.handlers = handlers;

    this.unsubs.push(
      onValue(ref(this.db, '.info/connected'), (snap) => {
        handlers.onConn((snap.val() === true ? 'connected' : 'offline') as ConnStatus);
      }),
    );

    this.unsubs.push(
      onValue(ref(this.db, 'helmets'), (snap) => {
        const raw = (snap.val() ?? {}) as Record<string, Record<string, unknown>>;
        const helmets: Record<string, Helmet> = {};
        for (const [id, v] of Object.entries(raw)) {
          helmets[id] = {
            id,
            name: (v.name as string) ?? id,
            status: v.status === 'online' ? 'online' : 'offline',
            lastSeen: typeof v.lastSeen === 'number' ? v.lastSeen : null,
            battery: typeof v.battery === 'number' ? v.battery : null,
          };
        }
        this.state.helmets = helmets;
        this.emit();
      }),
    );

    this.unsubs.push(
      onValue(ref(this.db, 'locations'), (snap) => {
        const raw = (snap.val() ?? {}) as Record<string, Record<string, unknown>>;
        const locations: Record<string, LocationPoint> = {};
        for (const [id, v] of Object.entries(raw)) {
          if (typeof v.lat === 'number' && typeof v.lng === 'number') {
            locations[id] = {
              helmetId: id,
              lat: v.lat,
              lng: v.lng,
              timestamp: typeof v.timestamp === 'number' && v.timestamp > 0 ? v.timestamp : Date.now(),
            };
          }
        }
        this.state.locations = locations;
        this.emit();
      }),
    );

    this.unsubs.push(
      onValue(ref(this.db, 'cameras'), (snap) => {
        const raw = (snap.val() ?? {}) as Record<string, Record<string, unknown>>;
        const cameras: Record<string, Camera> = {};
        for (const [id, v] of Object.entries(raw)) {
          const status: Camera['status'] =
            v.status === 'online' ? 'online' : v.status === 'mock' ? 'mock' : v.status === 'unconfigured' ? 'unconfigured' : 'offline';
          cameras[id] = {
            id: (v.id as string) ?? `CAM_${id.slice(-2)}`,
            helmetId: id,
            streamUrl: (v.streamUrl as string) ?? null,
            status,
          };
        }
        this.state.cameras = cameras;
        this.emit();
      }),
    );

    this.unsubs.push(
      onValue(ref(this.db, 'alerts'), (snap) => {
        const raw = (snap.val() ?? {}) as Record<string, Record<string, unknown>>;
        this.state.alerts = Object.entries(raw)
          .map(([id, v]) => this.normAlert(id, v))
          .sort((a, b) => b.timestamp - a.timestamp);
        this.emit();
      }),
    );

    this.unsubs.push(
      onChildAdded(ref(this.db, 'alerts'), (snap) => {
        const id = snap.key;
        if (!id) return;
        const a = this.normAlert(id, (snap.val() ?? {}) as Record<string, unknown>);
        if (!a.acknowledged) this.handlers?.onAlert(a);
      }),
    );

    const eventsQ = query(ref(this.db, 'events'), limitToLast(200));
    this.unsubs.push(
      onChildAdded(eventsQ, (snap) => {
        const e = this.normEvent(snap.key ?? uid(), (snap.val() ?? {}) as Record<string, unknown>);
        this.state.events = [e, ...this.state.events.filter((x) => x.id !== e.id)].slice(0, 200);
        this.state.events.sort((a, b) => b.timestamp - a.timestamp);
        this.handlers?.onEvent(e);
        this.emit();
      }),
    );

    for (const id of HELMET_IDS) {
      this.state.messages[id] = [];
      const mq = query(ref(this.db, `messages/${id}`), limitToLast(100));
      this.unsubs.push(
        onChildAdded(mq, (snap) => {
          const m = this.normMessage(id, snap.key ?? uid(), (snap.val() ?? {}) as Record<string, unknown>);
          const list = this.state.messages[id] ?? [];
          this.state.messages[id] = [...list.filter((x) => x.id !== m.id), m].slice(-100);
          this.handlers?.onMessage(m);
          this.emit();
        }),
      );
    }
  }

  sendMessage(helmetId: string, text: string): void {
    const payload = { helmetId, direction: 'gs_to_helmet', text, timestamp: Date.now(), status: 'sent' };
    void push(ref(this.db, `messages/${helmetId}`), payload);
  }

  acknowledgeAlert(alertId: string): void {
    void update(ref(this.db, `alerts/${alertId}`), { acknowledged: true, status: 'acknowledged' });
  }

  pushExternalLocation(helmetId: string, lat: number, lng: number): void {
    void set(ref(this.db, `locations/${helmetId}`), { helmetId, lat, lng, timestamp: Date.now() });
  }

  // mock-only controls
  triggerSos(): void { console.info('[REAL] triggerSos is a mock-only control'); }
  toggleHelmetOnline(): void { console.info('[REAL] toggleHelmetOnline is a mock-only control'); }
  toggleCamera(): void { console.info('[REAL] toggleCamera is a mock-only control'); }
  simulateLocation(): void { console.info('[REAL] simulateLocation is a mock-only control'); }

  dispose(): void {
    this.unsubs.forEach((u) => u());
    this.unsubs = [];
    this.handlers = null;
  }

  private emit(): void {
    this.handlers?.onState({
      helmets: { ...this.state.helmets },
      locations: { ...this.state.locations },
      cameras: { ...this.state.cameras },
      messages: { ...this.state.messages },
      alerts: [...this.state.alerts],
      events: [...this.state.events],
    });
  }

  private normAlert(id: string, v: Record<string, unknown>): Alert {
    return {
      id,
      helmetId: (v.helmetId as string) ?? 'UNKNOWN',
      type: (v.type as Alert['type']) ?? 'SOS',
      timestamp: typeof v.timestamp === 'number' && v.timestamp > 0 ? v.timestamp : Date.now(),
      status: v.acknowledged === true ? 'acknowledged' : 'active',
      acknowledged: v.acknowledged === true,
    };
  }

  private normEvent(id: string, v: Record<string, unknown>): TimelineEvent {
    return {
      id,
      helmetId: (v.helmetId as string) ?? 'UNKNOWN',
      type: (v.type as TimelineEvent['type']) ?? 'location_update',
      message: (v.message as string) ?? '',
      timestamp: typeof v.timestamp === 'number' && v.timestamp > 0 ? v.timestamp : Date.now(),
    };
  }

  private normMessage(helmetId: string, id: string, v: Record<string, unknown>): Message {
    return {
      id,
      helmetId,
      direction: v.direction === 'helmet_to_gs' ? 'helmet_to_gs' : 'gs_to_helmet',
      text: (v.text as string) ?? '',
      timestamp: typeof v.timestamp === 'number' && v.timestamp > 0 ? v.timestamp : Date.now(),
      status: (v.status as Message['status']) ?? 'sent',
    };
  }
}
'''

FILES["ground-station/src/mock/mockDataService.ts"] = r'''
import type { DataHandlers, DataService, StationState } from '../services/dataService';
import type { Alert, Camera, Helmet, LocationPoint, Message, TimelineEvent } from '../models/types';
import { HELMET_IDS } from '../models/constants';
import { truncate, uid } from '../utils/format';

interface WalkState { lat: number; lng: number; heading: number; }

const START: Record<string, WalkState> = {
  HELMET_01: { lat: 28.6125, lng: 77.2050, heading: 40 },
  HELMET_02: { lat: 28.6252, lng: 77.2190, heading: 140 },
  HELMET_03: { lat: 28.6052, lng: 77.1985, heading: 230 },
  HELMET_04: { lat: 28.6185, lng: 77.2305, heading: 320 },
};

const TICK_MS = 2000;
const MAX_EVENTS = 200;
const MAX_ALERTS = 100;
const MAX_MSGS = 100;

/** Full in-browser simulation. Everything it produces is MOCK. */
export class MockDataService implements DataService {
  readonly mode = 'MOCK' as const;
  private handlers: DataHandlers | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;
  private tick = 0;
  private state: StationState;

  constructor() {
    const now = Date.now();
    const helmets: Record<string, Helmet> = {};
    const locations: Record<string, LocationPoint> = {};
    const cameras: Record<string, Camera> = {};
    const messages: Record<string, Message[]> = {};
    HELMET_IDS.forEach((id, i) => {
      const n = id.slice(-2);
      helmets[id] = { id, name: `Helmet ${n}`, status: 'online', lastSeen: now, battery: 92 - i * 6 };
      locations[id] = { helmetId: id, lat: START[id].lat, lng: START[id].lng, timestamp: now };
      cameras[id] = { id: `CAM_${n}`, helmetId: id, streamUrl: null, status: 'mock' };
      messages[id] = [];
    });
    this.state = { helmets, locations, cameras, messages, alerts: [], events: [] };
  }

  start(handlers: DataHandlers): void {
    this.handlers = handlers;
    handlers.onConn('connected'); // mock layer is always "connected"
    handlers.onState(this.snapshot());
    this.timer = setInterval(() => this.onTick(), TICK_MS);
  }

  dispose(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.handlers = null;
  }

  sendMessage(helmetId: string, text: string): void {
    const m: Message = { id: uid(), helmetId, direction: 'gs_to_helmet', text, timestamp: Date.now(), status: 'sent' };
    this.pushMsg(helmetId, m);
    this.addEvent('message_sent', helmetId, `GS -> ${helmetId}: "${truncate(text, 36)}"`);
    this.emit();
    window.setTimeout(() => { m.status = 'delivered'; this.emit(); }, 1200);
    window.setTimeout(() => {
      const reply: Message = {
        id: uid(),
        helmetId,
        direction: 'helmet_to_gs',
        text: `[MOCK] ${this.hname(helmetId)} received: "${truncate(text, 18)}"`,
        timestamp: Date.now(),
        status: 'delivered',
      };
      this.pushMsg(helmetId, reply);
      this.addEvent('message_received', helmetId, `${helmetId} acknowledged GS message`);
      this.handlers?.onMessage(reply);
      this.emit();
    }, 2600);
  }

  acknowledgeAlert(alertId: string): void {
    const a = this.state.alerts.find((x) => x.id === alertId);
    if (!a || a.acknowledged) return;
    a.acknowledged = true;
    a.status = 'acknowledged';
    this.addEvent('alert_acknowledged', a.helmetId, `${a.type} alert acknowledged by operator`);
    this.emit();
  }

  triggerSos(helmetId: string): void {
    const a: Alert = { id: uid(), helmetId, type: 'SOS', timestamp: Date.now(), status: 'active', acknowledged: false };
    this.state.alerts = [a, ...this.state.alerts].slice(0, MAX_ALERTS);
    this.addEvent('sos_triggered', helmetId, `${helmetId} SOS triggered (mock button)`);
    this.handlers?.onAlert(a);
    this.emit();
  }

  toggleHelmetOnline(helmetId: string): void {
    const h = this.state.helmets[helmetId];
    if (!h) return;
    if (h.status === 'online') {
      h.status = 'offline';
      h.lastSeen = Date.now();
      this.addEvent('helmet_offline', helmetId, `${helmetId} went offline`);
    } else {
      h.status = 'online';
      h.lastSeen = Date.now();
      this.addEvent('helmet_online', helmetId, `${helmetId} came online`);
    }
    this.emit();
  }

  toggleCamera(helmetId: string): void {
    const c = this.state.cameras[helmetId];
    if (!c) return;
    if (c.status === 'mock') {
      c.status = 'offline';
      this.addEvent('camera_offline', helmetId, `${c.id} mock feed went offline`);
    } else {
      c.status = 'mock';
      this.addEvent('camera_online', helmetId, `${c.id} mock feed online`);
    }
    this.emit();
  }

  simulateLocation(helmetId: string): void {
    const loc = this.state.locations[helmetId];
    if (!loc) return;
    loc.lat += (Math.random() - 0.5) * 0.02;
    loc.lng += (Math.random() - 0.5) * 0.02;
    loc.timestamp = Date.now();
    this.addEvent('location_update', helmetId, `Simulated GPS jump -> ${loc.lat.toFixed(5)}, ${loc.lng.toFixed(5)}`);
    this.emit();
  }

  pushExternalLocation(helmetId: string, lat: number, lng: number): void {
    const loc = this.state.locations[helmetId];
    if (!loc) return;
    loc.lat = lat;
    loc.lng = lng;
    loc.timestamp = Date.now();
    const h = this.state.helmets[helmetId];
    if (h) h.lastSeen = loc.timestamp;
    this.addEvent('location_update', helmetId, `External GPS push -> ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    this.emit();
  }

  // -- internals --

  private hname(id: string): string { return `Helmet ${id.slice(-2)}`; }

  private pushMsg(helmetId: string, m: Message): void {
    const list = this.state.messages[helmetId] ?? [];
    this.state.messages[helmetId] = [...list, m].slice(-MAX_MSGS);
  }

  private addEvent(type: TimelineEvent['type'], helmetId: string, message: string): void {
    const e: TimelineEvent = { id: uid(), helmetId, type, message, timestamp: Date.now() };
    this.state.events = [e, ...this.state.events].slice(0, MAX_EVENTS);
    this.handlers?.onEvent(e);
  }

  private snapshot(): StationState {
    return JSON.parse(JSON.stringify(this.state)) as StationState;
  }

  private emit(): void {
    this.handlers?.onState(this.snapshot());
  }

  private onTick(): void {
    this.tick++;
    const now = Date.now();
    HELMET_IDS.forEach((id) => {
      const h = this.state.helmets[id];
      if (h.status !== 'online') return;
      const w = START[id];
      w.heading += Math.random() * 50 - 25;
      const step = 0.00028; // ~30 m per tick
      w.lat += Math.cos((w.heading * Math.PI) / 180) * step;
      w.lng += Math.sin((w.heading * Math.PI) / 180) * step;
      const loc = this.state.locations[id];
      loc.lat = w.lat;
      loc.lng = w.lng;
      loc.timestamp = now;
      h.lastSeen = now;
      if (h.battery != null) h.battery = Math.max(5, h.battery - 0.02);
      if (this.tick % 10 === Math.floor(Math.random() * 10)) {
        this.addEvent('location_update', id, `GPS -> ${loc.lat.toFixed(5)}, ${loc.lng.toFixed(5)}`);
      }
    });
    this.emit();
  }
}
'''

FILES["ground-station/src/location/locationProvider.ts"] = r'''
/**
 * Location abstraction: phone GPS feeds Firebase, Firebase feeds the map.
 * No GPS hardware (no NEO-6M) anywhere in this system.
 */
export interface LocationFix {
  lat: number;
  lng: number;
  accuracy?: number;
  timestamp: number;
  source: 'mock' | 'phone';
}

export interface LocationProvider {
  readonly name: 'MOCK_GPS' | 'PHONE_GPS';
  isAvailable(): boolean;
  getCurrentFix(): Promise<LocationFix>;
}
'''

FILES["ground-station/src/location/mockLocationProvider.ts"] = r'''
import type { LocationFix, LocationProvider } from './locationProvider';

export class MockLocationProvider implements LocationProvider {
  readonly name = 'MOCK_GPS' as const;
  private t = 0;

  isAvailable(): boolean { return true; }

  getCurrentFix(): Promise<LocationFix> {
    this.t += 0.012;
    const fix: LocationFix = {
      lat: 28.6139 + Math.sin(this.t) * 0.012,
      lng: 77.2090 + Math.cos(this.t) * 0.012,
      timestamp: Date.now(),
      source: 'mock',
    };
    return Promise.resolve(fix);
  }
}
'''

FILES["ground-station/src/location/phoneLocationProvider.ts"] = r'''
import type { LocationFix, LocationProvider } from './locationProvider';

/**
 * REAL phone GPS via the browser Geolocation API (works on the device
 * running the Ground Station, e.g. a phone/tablet). Feeds Firebase.
 */
export class PhoneLocationProvider implements LocationProvider {
  readonly name = 'PHONE_GPS' as const;

  isAvailable(): boolean {
    return typeof navigator !== 'undefined' && 'geolocation' in navigator;
  }

  getCurrentFix(): Promise<LocationFix> {
    return new Promise((resolve, reject) => {
      if (!this.isAvailable()) {
        reject(new Error('Geolocation API unavailable'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) =>
          resolve({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            timestamp: pos.timestamp,
            source: 'phone',
          }),
        (err) => reject(err),
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 },
      );
    });
  }
}
'''

FILES["ground-station/src/utils/format.ts"] = r'''
export const uid = (): string => Math.random().toString(36).slice(2, 10);

export function fmtTime(ts: number | null): string {
  if (!ts) return '—';
  return new Date(ts).toLocaleTimeString([], { hour12: false });
}

export function fmtAgo(ts: number | null): string {
  if (!ts) return 'never';
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}

export function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + '…' : s;
}
'''

FILES["ground-station/src/utils/camera.ts"] = r'''
import { cameraStreamUrls } from '../firebase/config';
import type { Camera } from '../models/types';

export interface CamState {
  mode: 'REAL' | 'MOCK' | 'OFFLINE';
  url: string | null;
}

/**
 * Resolves what a CCTV tile should show. Never claims REAL unless a real
 * stream URL exists (env var or RTDB) and the camera isn't marked offline.
 */
export function cameraState(cam: Camera | undefined, helmetId: string): CamState {
  const envUrl = cameraStreamUrls[helmetId] || cam?.streamUrl || '';
  const status = cam?.status ?? 'offline';
  if (envUrl && status !== 'offline') return { mode: 'REAL', url: envUrl };
  if (status === 'mock') return { mode: 'MOCK', url: null };
  return { mode: 'OFFLINE', url: null };
}
'''

FILES["ground-station/src/hooks/useStation.ts"] = r'''
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ConnStatus, DataService, StationState } from '../services/dataService';
import { RealDataService } from '../services/realDataService';
import { MockDataService } from '../mock/mockDataService';
import { isRealMode } from '../firebase/config';
import { uid } from '../utils/format';

export interface Toast {
  id: string;
  kind: 'sos' | 'info' | 'warn' | 'ok';
  text: string;
}

const EMPTY: StationState = { helmets: {}, locations: {}, cameras: {}, messages: {}, alerts: [], events: [] };

export function useStation() {
  const [state, setState] = useState<StationState>(EMPTY);
  const [conn, setConn] = useState<ConnStatus>('connecting');
  const [toasts, setToasts] = useState<Toast[]>([]);
  // suppress toast spam from the initial RTDB backlog on startup
  const quietUntil = useRef(Date.now() + 3000);

  const service = useMemo<DataService>(
    () => (isRealMode ? new RealDataService() : new MockDataService()),
    [],
  );

  const pushToast = useCallback((kind: Toast['kind'], text: string, ttl = 5000) => {
    const id = uid();
    setToasts((prev) => [...prev.slice(-4), { id, kind, text }]);
    window.setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), ttl);
  }, []);

  useEffect(() => {
    quietUntil.current = Date.now() + 3000;
    service.start({
      onState: setState,
      onConn: setConn,
      onEvent: (e) => {
        if (Date.now() < quietUntil.current) return;
        switch (e.type) {
          case 'helmet_online': pushToast('ok', `${e.helmetId} is ONLINE`); break;
          case 'helmet_offline': pushToast('warn', `${e.helmetId} went OFFLINE`); break;
          case 'camera_online': pushToast('ok', `${e.helmetId} camera online`); break;
          case 'camera_offline': pushToast('warn', `${e.helmetId} camera offline`); break;
          default: break;
        }
      },
      onAlert: (a) => {
        if (Date.now() < quietUntil.current) return;
        pushToast('sos', `SOS! ${a.helmetId} · ${a.type} · ${new Date(a.timestamp).toLocaleTimeString()}`, 12000);
      },
      onMessage: (m) => {
        if (Date.now() < quietUntil.current) return;
        if (m.direction === 'helmet_to_gs') pushToast('info', `Message from ${m.helmetId}: ${m.text.slice(0, 40)}`);
      },
    });
    return () => service.dispose();
  }, [service, pushToast]);

  return { state, conn, toasts, service, mode: service.mode };
}
'''

# ---------------------- ground-station components ----------------------
FILES["ground-station/src/components/Header.tsx"] = r'''
import { useEffect, useState } from 'react';
import type { ConnStatus } from '../services/dataService';

interface Props {
  mode: 'REAL' | 'MOCK';
  conn: ConnStatus;
  onlineCount: number;
  total: number;
}

export default function Header({ mode, conn, onlineCount, total }: Props) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const i = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(i);
  }, []);

  const fbLabel =
    mode === 'MOCK' ? 'FIREBASE: MOCK'
      : conn === 'connected' ? 'FIREBASE: LIVE'
      : conn === 'connecting' ? 'FIREBASE: CONNECTING'
      : 'FIREBASE: OFFLINE';
  const fbClass = mode === 'MOCK' ? 'badge mock' : conn === 'connected' ? 'badge ok' : conn === 'connecting' ? 'badge warn' : 'badge bad';

  return (
    <header className="header">
      <div className="brand">
        <div className="brand-mark" />
        <div>
          <div className="brand-title">SIH SMART HELMET</div>
          <div className="brand-sub">GROUND CONTROL STATION</div>
        </div>
      </div>
      <div className="header-badges">
        <span className={`badge ${mode === 'REAL' ? 'ok' : 'mock'}`}>MODE: {mode}</span>
        <span className={fbClass}>{fbLabel}</span>
        <span className={`badge ${onlineCount > 0 ? 'ok' : 'bad'}`}>{onlineCount}/{total} HELMETS ONLINE</span>
        <span className="badge dim">{now.toLocaleTimeString([], { hour12: false })}</span>
      </div>
    </header>
  );
}
'''

FILES["ground-station/src/components/HelmetList.tsx"] = r'''
import type { StationState } from '../services/dataService';
import { HELMET_IDS, helmetName } from '../models/constants';
import { fmtAgo } from '../utils/format';

interface Props { state: StationState; selectedId: string; onSelect: (id: string) => void; }

export default function HelmetList({ state, selectedId, onSelect }: Props) {
  return (
    <section className="panel">
      <div className="panel-h">
        <span>Helmet Fleet</span>
        <span className="pill dim">{HELMET_IDS.length} UNITS</span>
      </div>
      <div className="helmet-list">
        {HELMET_IDS.map((id) => {
          const h = state.helmets[id];
          const online = h?.status === 'online';
          return (
            <button
              key={id}
              className={`helmet-item ${id === selectedId ? 'selected' : ''}`}
              onClick={() => onSelect(id)}
            >
              <span className={`dot ${online ? 'ok' : 'bad'}`} />
              <span className="hi-name">{helmetName(id)}</span>
              <span className="hi-meta">
                {online ? 'ONLINE' : 'OFFLINE'} · {fmtAgo(h?.lastSeen ?? null)}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
'''

FILES["ground-station/src/components/MapPanel.tsx"] = r'''
import { useEffect } from 'react';
import L from 'leaflet';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { StationState } from '../services/dataService';
import { HELMET_IDS, helmetName, MAP_CENTER } from '../models/constants';
import { fmtAgo } from '../utils/format';

interface Props { state: StationState; selectedId: string; onSelect: (id: string) => void; }

function MapFocus({ lat, lng, keyId }: { lat: number; lng: number; keyId: string }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lng], Math.max(map.getZoom(), 14), { duration: 0.8 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keyId]);
  return null;
}

export default function MapPanel({ state, selectedId, onSelect }: Props) {
  const selectedLoc = state.locations[selectedId];
  return (
    <section className="panel map-panel">
      <div className="panel-h">
        <span>Live Map</span>
        <span className="pill dim">{selectedLoc ? 'GPS DATA · OSM TILES' : 'NO FIX'}</span>
      </div>
      <div className="map-wrap">
        <MapContainer center={MAP_CENTER} zoom={13} scrollWheelZoom>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {HELMET_IDS.map((id) => {
            const loc = state.locations[id];
            const h = state.helmets[id];
            if (!loc || !h) return null;
            const online = h.status === 'online';
            const sel = id === selectedId;
            const icon = L.divIcon({
              className: 'hm-wrap',
              html: `<div class="hm ${online ? 'online' : 'offline'} ${sel ? 'selected' : ''}"><span>${id.slice(-2)}</span></div>`,
              iconSize: [36, 36],
              iconAnchor: [18, 18],
            });
            return (
              <Marker key={id} position={[loc.lat, loc.lng]} icon={icon} eventHandlers={{ click: () => onSelect(id) }}>
                <Popup>
                  <div className="popup">
                    <strong>{helmetName(id)}</strong>
                    <div>STATUS: {online ? 'ONLINE' : 'OFFLINE'}</div>
                    <div>LAT: {loc.lat.toFixed(6)}</div>
                    <div>LNG: {loc.lng.toFixed(6)}</div>
                    <div>UPDATED: {fmtAgo(loc.timestamp)}</div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
          {selectedLoc && <MapFocus lat={selectedLoc.lat} lng={selectedLoc.lng} keyId={selectedId} />}
        </MapContainer>
      </div>
    </section>
  );
}
'''

FILES["ground-station/src/components/CctvGrid.tsx"] = r'''
import { useEffect, useState } from 'react';
import type { StationState } from '../services/dataService';
import { HELMET_IDS, helmetName } from '../models/constants';
import { cameraState } from '../utils/camera';

interface Props { state: StationState; selectedId: string; onSelect: (id: string) => void; }

function MockFeed() {
  const [t, setT] = useState(() => new Date());
  useEffect(() => {
    const i = setInterval(() => setT(new Date()), 1000);
    return () => clearInterval(i);
  }, []);
  return (
    <div className="mock-feed">
      <div className="mock-noise" />
      <div className="mock-scan" />
      <div className="mock-osd">
        <span>MOCK FEED · SIMULATED</span>
        <span>{t.toLocaleTimeString([], { hour12: false })}</span>
      </div>
    </div>
  );
}

export default function CctvGrid({ state, selectedId, onSelect }: Props) {
  const [enlarged, setEnlarged] = useState<string | null>(null);

  return (
    <section className="panel">
      <div className="panel-h">
        <span>CCTV Surveillance</span>
        <span className="pill dim">CLICK FEED TO ENLARGE</span>
      </div>
      <div className={`cctv-grid ${enlarged ? 'has-enlarged' : ''}`}>
        {HELMET_IDS.map((id) => {
          const cs = cameraState(state.cameras[id], id);
          const sel = id === selectedId;
          const big = enlarged === id;
          return (
            <div key={id} className={`cctv ${sel ? 'selected' : ''} ${big ? 'enlarged' : ''}`} onClick={() => onSelect(id)}>
              <div className="cctv-h">
                <span>CAM {id.slice(-2)} · {helmetName(id)}</span>
                <span className={`badge ${cs.mode === 'REAL' ? 'ok' : cs.mode === 'MOCK' ? 'mock' : 'bad'}`}>{cs.mode}</span>
              </div>
              <div
                className="cctv-body"
                onClick={(e) => {
                  e.stopPropagation();
                  setEnlarged(big ? null : id);
                }}
              >
                {cs.mode === 'REAL' && cs.url ? (
                  <img className="cctv-stream" src={cs.url} alt={`${helmetName(id)} live stream`} />
                ) : cs.mode === 'MOCK' ? (
                  <MockFeed />
                ) : (
                  <div className="cctv-offline">NO SIGNAL</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
'''

FILES["ground-station/src/components/AlertsPanel.tsx"] = r'''
import type { Alert } from '../models/types';
import { fmtTime } from '../utils/format';

interface Props {
  alerts: Alert[];
  selectedId: string;
  onSelect: (id: string) => void;
  onAck: (id: string) => void;
}

export default function AlertsPanel({ alerts, selectedId, onSelect, onAck }: Props) {
  const sorted = [...alerts].sort((a, b) => {
    if (a.acknowledged !== b.acknowledged) return a.acknowledged ? 1 : -1;
    return b.timestamp - a.timestamp;
  });
  const activeCount = sorted.filter((a) => !a.acknowledged).length;

  return (
    <section className="panel">
      <div className="panel-h">
        <span>SOS / Alerts</span>
        <span className={`pill ${activeCount > 0 ? 'bad' : 'dim'}`}>{activeCount} ACTIVE</span>
      </div>
      <div className="alert-list">
        {sorted.length === 0 && <div className="empty">No alerts. System nominal.</div>}
        {sorted.map((a) => (
          <div key={a.id} className={`alert ${a.acknowledged ? 'acked' : 'active'} ${a.helmetId === selectedId ? 'for-selected' : ''}`}>
            <div className="alert-top">
              <span className={`badge ${a.acknowledged ? 'dim' : 'bad'}`}>{a.type}</span>
              <button className="link" onClick={() => onSelect(a.helmetId)}>{a.helmetId}</button>
              <span className="alert-time">{fmtTime(a.timestamp)}</span>
            </div>
            <div className="alert-bottom">
              <span className="alert-status">{a.acknowledged ? 'ACKNOWLEDGED' : 'UNACKNOWLEDGED'}</span>
              {!a.acknowledged && (
                <button className="btn small danger" onClick={() => onAck(a.id)}>ACKNOWLEDGE</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
'''

FILES["ground-station/src/components/MessagingPanel.tsx"] = r'''
import { useState } from 'react';
import type { Message } from '../models/types';
import { helmetName } from '../models/constants';
import { fmtTime } from '../utils/format';

interface Props { helmetId: string; messages: Message[]; onSend: (text: string) => void; }

export default function MessagingPanel({ helmetId, messages, onSend }: Props) {
  const [text, setText] = useState('');
  const send = () => {
    const t = text.trim();
    if (!t) return;
    onSend(t);
    setText('');
  };

  return (
    <section className="panel">
      <div className="panel-h">
        <span>Messaging · {helmetName(helmetId)}</span>
        <span className="pill dim">{messages.length} MSG</span>
      </div>
      <div className="msg-list">
        {messages.length === 0 && <div className="empty">No messages yet.</div>}
        {messages.map((m) => (
          <div key={m.id} className={`msg ${m.direction}`}>
            <div className="msg-bubble">
              <div className="msg-text">{m.text}</div>
              <div className="msg-meta">
                {fmtTime(m.timestamp)} · {m.direction === 'gs_to_helmet' ? 'GS→HELMET' : 'HELMET→GS'} · {m.status.toUpperCase()}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="msg-input">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder={`Message ${helmetName(helmetId)}…`}
          maxLength={120}
        />
        <button className="btn" onClick={send}>SEND</button>
      </div>
    </section>
  );
}
'''

FILES["ground-station/src/components/DetailsPanel.tsx"] = r'''
import type { ReactNode } from 'react';
import type { StationState } from '../services/dataService';
import { helmetName } from '../models/constants';
import { cameraState } from '../utils/camera';
import { fmtAgo, fmtTime, truncate } from '../utils/format';

interface RowProps { k: string; v: ReactNode; cls?: string; }

function Row({ k, v, cls }: RowProps) {
  return (
    <div className="row">
      <span className="rk">{k}</span>
      <span className={`rv ${cls ?? ''}`}>{v}</span>
    </div>
  );
}

export default function DetailsPanel({ state, helmetId }: { state: StationState; helmetId: string }) {
  const h = state.helmets[helmetId];
  const loc = state.locations[helmetId];
  const cam = cameraState(state.cameras[helmetId], helmetId);
  const msgs = state.messages[helmetId] ?? [];
  const lastMsg = msgs[msgs.length - 1];
  const lastEvt = state.events.find((e) => e.helmetId === helmetId);
  const sosActive = state.alerts.some((a) => a.helmetId === helmetId && !a.acknowledged);

  return (
    <section className="panel">
      <div className="panel-h">
        <span>Helmet Details · {helmetName(helmetId)}</span>
        <span className={`badge ${h?.status === 'online' ? 'ok' : 'bad'}`}>
          {h ? h.status.toUpperCase() : 'UNKNOWN'}
        </span>
      </div>
      <div className="details">
        <Row k="HELMET ID" v={helmetId} />
        <Row k="ONLINE" v={h ? (h.status === 'online' ? 'YES' : 'NO') : '—'} cls={h?.status === 'online' ? 'ok-text' : 'bad-text'} />
        <Row k="LATITUDE" v={loc ? loc.lat.toFixed(6) : '—'} />
        <Row k="LONGITUDE" v={loc ? loc.lng.toFixed(6) : '—'} />
        <Row k="LAST LOCATION UPDATE" v={loc ? `${fmtTime(loc.timestamp)} (${fmtAgo(loc.timestamp)})` : '—'} />
        <Row k="BATTERY" v={h?.battery != null ? `${Math.round(h.battery)}%` : 'not reported'} />
        <Row k="CAMERA" v={cam.mode} cls={cam.mode === 'REAL' ? 'ok-text' : cam.mode === 'MOCK' ? 'warn-text' : 'bad-text'} />
        <Row k="SOS STATE" v={sosActive ? 'SOS ACTIVE' : 'CLEAR'} cls={sosActive ? 'bad-text blink' : 'ok-text'} />
        <Row k="LAST EVENT" v={lastEvt ? `${lastEvt.type} · ${fmtAgo(lastEvt.timestamp)}` : '—'} />
        <Row k="LAST MESSAGE" v={lastMsg ? truncate(lastMsg.text, 30) : '—'} />
      </div>
    </section>
  );
}
'''

FILES["ground-station/src/components/TimelinePanel.tsx"] = r'''
import type { TimelineEvent } from '../models/types';
import { fmtAgo } from '../utils/format';

const LABEL: Record<string, string> = {
  helmet_online: 'ONLINE',
  helmet_offline: 'OFFLINE',
  location_update: 'GPS',
  sos_triggered: 'SOS',
  alert_acknowledged: 'ACK',
  message_sent: 'MSG →',
  message_received: 'MSG ←',
  camera_online: 'CAM ON',
  camera_offline: 'CAM OFF',
};

export default function TimelinePanel({ events, helmetId }: { events: TimelineEvent[]; helmetId: string }) {
  const list = events.filter((e) => e.helmetId === helmetId).slice(0, 40);
  return (
    <section className="panel">
      <div className="panel-h">
        <span>Activity Timeline</span>
        <span className="pill dim">{helmetId}</span>
      </div>
      <div className="timeline">
        {list.length === 0 && <div className="empty">No activity for this helmet yet.</div>}
        {list.map((e) => (
          <div key={e.id} className={`tl-item t-${e.type}`}>
            <span className="tl-dot" />
            <div className="tl-body">
              <div className="tl-head">
                <span className="tl-type">{LABEL[e.type] ?? e.type}</span>
                <span className="tl-time">{fmtAgo(e.timestamp)}</span>
              </div>
              <div className="tl-msg">{e.message}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
'''

FILES["ground-station/src/components/Toasts.tsx"] = r'''
import type { Toast } from '../hooks/useStation';

export default function Toasts({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="toasts">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.kind}`}>{t.text}</div>
      ))}
    </div>
  );
}
'''

FILES["ground-station/src/components/DemoControls.tsx"] = r'''
import { useState } from 'react';
import type { DataService } from '../services/dataService';
import { helmetName } from '../models/constants';
import { MockLocationProvider } from '../location/mockLocationProvider';
import { PhoneLocationProvider } from '../location/phoneLocationProvider';

interface Props { helmetId: string; service: DataService; }

export default function DemoControls({ helmetId, service }: Props) {
  const [gpsMsg, setGpsMsg] = useState<string | null>(null);

  const pushDeviceGps = async () => {
    const phone = new PhoneLocationProvider();
    try {
      const fix = phone.isAvailable() ? await phone.getCurrentFix() : await new MockLocationProvider().getCurrentFix();
      service.pushExternalLocation(helmetId, fix.lat, fix.lng);
      setGpsMsg(`${fix.source === 'phone' ? 'PHONE_GPS' : 'MOCK_GPS'}: ${fix.lat.toFixed(5)}, ${fix.lng.toFixed(5)}`);
    } catch {
      const fix = await new MockLocationProvider().getCurrentFix();
      service.pushExternalLocation(helmetId, fix.lat, fix.lng);
      setGpsMsg(`MOCK_GPS fallback: ${fix.lat.toFixed(5)}, ${fix.lng.toFixed(5)}`);
    }
    setTimeout(() => setGpsMsg(null), 4000);
  };

  return (
    <div className="demo-bar">
      <span className="demo-label">DEMO CONTROLS (MOCK) · TARGET: {helmetName(helmetId).toUpperCase()}</span>
      <button className="btn danger" onClick={() => service.triggerSos(helmetId)}>TRIGGER SOS</button>
      <button className="btn" onClick={() => service.toggleHelmetOnline(helmetId)}>TOGGLE ONLINE</button>
      <button className="btn" onClick={() => service.toggleCamera(helmetId)}>TOGGLE CAMERA</button>
      <button className="btn" onClick={() => service.simulateLocation(helmetId)}>SIMULATE LOCATION</button>
      <button className="btn" onClick={pushDeviceGps}>PUSH THIS DEVICE GPS</button>
      {gpsMsg && <span className="demo-gps">{gpsMsg}</span>}
    </div>
  );
}
'''

FILES["ground-station/src/styles/global.css"] = r'''
:root {
  --bg: #0a0e13;
  --panel: #10161f;
  --panel2: #0d131b;
  --line: #1d2836;
  --text: #d7e1ec;
  --dim: #7c8b9d;
  --accent: #37e0c8;
  --red: #ff4d5e;
  --amber: #ffb547;
  --green: #3ddc84;
  --blue: #4aa8ff;
}
* { box-sizing: border-box; }
html, body, #root { height: 100%; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  font-size: 14px;
}
button { font-family: inherit; }

.app { min-height: 100vh; display: flex; flex-direction: column; }

.header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding: 10px 16px; border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, #0e141d, #0a0e13);
  flex-wrap: wrap;
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand-mark {
  width: 34px; height: 34px; border-radius: 8px;
  background: linear-gradient(135deg, var(--accent), #1b6f8f);
  box-shadow: 0 0 14px #37e0c855;
}
.brand-title { font-weight: 800; letter-spacing: .12em; font-size: 15px; }
.brand-sub { font-size: 10px; letter-spacing: .28em; color: var(--dim); }
.header-badges { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }

.badge {
  font-size: 10px; font-weight: 700; letter-spacing: .1em;
  padding: 4px 9px; border-radius: 4px; border: 1px solid var(--line);
  background: var(--panel2); color: var(--dim); white-space: nowrap;
}
.badge.ok   { color: var(--green); border-color: #1d4a33; background: #0f2018; }
.badge.bad  { color: var(--red);   border-color: #55232b; background: #230f14; }
.badge.warn { color: var(--amber); border-color: #55422a; background: #231a0f; }
.badge.mock { color: var(--amber); border-color: #55422a; background: repeating-linear-gradient(45deg,#231a0f,#231a0f 6px,#2a1f12 6px,#2a1f12 12px); }
.badge.dim  { opacity: .8; }

.mock-banner {
  padding: 7px 16px; font-size: 12px; color: var(--amber);
  background: #231a0f; border-bottom: 1px solid #55422a;
}

.layout {
  display: grid; grid-template-columns: 300px minmax(0, 1fr) 340px;
  gap: 12px; padding: 12px; flex: 1; align-items: start;
}
.col { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
@media (max-width: 1280px) {
  .layout { grid-template-columns: 1fr 1fr; }
  .col-right { grid-column: 1 / -1; }
}
@media (max-width: 860px) { .layout { grid-template-columns: 1fr; } }

.panel {
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 8px; overflow: hidden; display: flex; flex-direction: column;
}
.panel-h {
  padding: 8px 12px; border-bottom: 1px solid var(--line);
  display: flex; justify-content: space-between; align-items: center; gap: 8px;
  font-size: 11px; letter-spacing: .12em; color: var(--dim); text-transform: uppercase;
}
.pill {
  font-size: 10px; letter-spacing: .08em; padding: 2px 8px;
  border-radius: 10px; border: 1px solid var(--line);
}
.pill.bad { color: var(--red); border-color: #55232b; }
.pill.dim { color: var(--dim); }
.empty { padding: 14px; color: var(--dim); font-size: 12px; }

.helmet-list { display: flex; flex-direction: column; }
.helmet-item {
  display: grid; grid-template-columns: auto 1fr; grid-template-rows: auto auto;
  column-gap: 10px; row-gap: 2px; text-align: left; width: 100%;
  padding: 10px 12px; background: transparent; border: none;
  border-bottom: 1px solid var(--line); color: var(--text); cursor: pointer;
}
.helmet-item:hover { background: #131c27; }
.helmet-item.selected { background: #10202a; box-shadow: inset 3px 0 0 var(--accent); }
.dot { grid-row: 1 / span 2; align-self: center; width: 10px; height: 10px; border-radius: 50%; }
.dot.ok { background: var(--green); box-shadow: 0 0 8px #3ddc8488; }
.dot.bad { background: #5b6673; }
.hi-name { font-weight: 700; letter-spacing: .04em; }
.helmet-item.selected .hi-name { color: var(--accent); }
.hi-meta { font-size: 11px; color: var(--dim); }

.map-wrap { height: 420px; }
.leaflet-container { height: 100%; width: 100%; background: #0a0e13; font: inherit; }
.leaflet-popup-content-wrapper { background: var(--panel); color: var(--text); border: 1px solid var(--line); }
.leaflet-popup-tip { background: var(--panel); }
.popup div { font-size: 12px; }

.hm-wrap { background: transparent; border: none; }
.hm {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid #5b6673; background: #0d131bcc;
  font-weight: 800; font-size: 11px; color: #93a1b1;
  transition: transform .15s;
}
.hm.online { border-color: var(--green); color: var(--green); box-shadow: 0 0 10px #3ddc8466; }
.hm.offline { opacity: .6; }
.hm.selected { border-color: var(--accent); color: var(--accent); box-shadow: 0 0 16px #37e0c8aa; transform: scale(1.18); }

.cctv-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 10px; }
.cctv { border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: var(--panel2); cursor: pointer; }
.cctv.selected { border-color: var(--accent); box-shadow: 0 0 10px #37e0c844; }
.cctv.enlarged { grid-column: 1 / -1; }
.cctv-h {
  display: flex; justify-content: space-between; align-items: center; gap: 6px;
  padding: 6px 8px; font-size: 10px; letter-spacing: .1em; color: var(--dim);
  border-bottom: 1px solid var(--line);
}
.cctv-body { position: relative; height: 150px; background: #05070a; }
.cctv.enlarged .cctv-body { height: 320px; }
.cctv-stream { width: 100%; height: 100%; object-fit: cover; display: block; }
.cctv-offline {
  height: 100%; display: flex; align-items: center; justify-content: center;
  color: #55606d; letter-spacing: .3em; font-size: 12px; font-weight: 700;
}
.mock-feed { position: absolute; inset: 0; overflow: hidden; }
.mock-noise {
  position: absolute; inset: -8px; opacity: .22;
  background-image: repeating-conic-gradient(#8b98a5 0 .0008turn, #10151c .0008turn .0016turn);
  background-size: 3px 3px;
  animation: noiseShift .3s steps(3) infinite;
}
@keyframes noiseShift {
  0% { transform: translate(0,0); }
  33% { transform: translate(-2px,1px); }
  66% { transform: translate(1px,-2px); }
  100% { transform: translate(0,0); }
}
.mock-scan {
  position: absolute; inset: 0;
  background: repeating-linear-gradient(0deg, transparent 0 2px, #0004 2px 4px);
}
.mock-osd {
  position: absolute; left: 0; right: 0; bottom: 0;
  display: flex; justify-content: space-between; padding: 4px 8px;
  font-size: 10px; letter-spacing: .08em; color: var(--amber);
  background: #0009;
}

.alert-list { display: flex; flex-direction: column; max-height: 340px; overflow-y: auto; }
.alert { padding: 10px 12px; border-bottom: 1px solid var(--line); }
.alert.active { background: #1c0f13; }
.alert.active.for-selected { box-shadow: inset 3px 0 0 var(--red); }
.alert.acked { opacity: .55; }
.alert-top { display: flex; align-items: center; gap: 8px; }
.alert-time { margin-left: auto; font-size: 11px; color: var(--dim); }
.alert-bottom { display: flex; align-items: center; justify-content: space-between; margin-top: 6px; }
.alert-status { font-size: 10px; letter-spacing: .12em; color: var(--dim); }

.btn {
  padding: 7px 14px; border-radius: 5px; border: 1px solid var(--line);
  background: #16212e; color: var(--text); font-weight: 700;
  font-size: 11px; letter-spacing: .1em; cursor: pointer;
}
.btn:hover { border-color: var(--accent); color: var(--accent); }
.btn.danger { background: #2a1116; border-color: #55232b; color: var(--red); }
.btn.danger:hover { border-color: var(--red); box-shadow: 0 0 10px #ff4d5e44; }
.btn.small { padding: 4px 10px; font-size: 10px; }
.link { background: none; border: none; color: var(--blue); cursor: pointer; padding: 0; font-size: 12px; }

.msg-list { display: flex; flex-direction: column; gap: 8px; padding: 12px; max-height: 260px; overflow-y: auto; }
.msg { display: flex; }
.msg.gs_to_helmet { justify-content: flex-end; }
.msg.helmet_to_gs { justify-content: flex-start; }
.msg-bubble {
  max-width: 82%; padding: 8px 10px; border-radius: 8px;
  background: var(--panel2); border: 1px solid var(--line);
}
.msg.gs_to_helmet .msg-bubble { background: #10222c; border-color: #1c4653; }
.msg.helmet_to_gs .msg-bubble { background: #161d29; }
.msg-text { font-size: 13px; word-break: break-word; }
.msg-meta { margin-top: 4px; font-size: 9px; letter-spacing: .08em; color: var(--dim); }
.msg-input { display: flex; gap: 8px; padding: 10px 12px; border-top: 1px solid var(--line); }
.msg-input input {
  flex: 1; background: var(--panel2); border: 1px solid var(--line);
  border-radius: 5px; color: var(--text); padding: 8px 10px; font-size: 13px;
}
.msg-input input:focus { outline: none; border-color: var(--accent); }

.details { padding: 6px 0; }
.row { display: flex; justify-content: space-between; gap: 10px; padding: 6px 12px; }
.row:nth-child(odd) { background: #0d131b; }
.rk { font-size: 10px; letter-spacing: .12em; color: var(--dim); padding-top: 2px; }
.rv { font-size: 13px; text-align: right; word-break: break-word; }
.ok-text { color: var(--green); }
.warn-text { color: var(--amber); }
.bad-text { color: var(--red); }
.blink { animation: blink 1s steps(2) infinite; }
@keyframes blink { 50% { opacity: .35; } }

.timeline { max-height: 300px; overflow-y: auto; padding: 6px 0; }
.tl-item { display: flex; gap: 10px; padding: 7px 12px; }
.tl-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--dim); margin-top: 5px; flex: none; }
.t-sos_triggered .tl-dot { background: var(--red); box-shadow: 0 0 8px var(--red); }
.t-helmet_online .tl-dot, .t-camera_online .tl-dot { background: var(--green); }
.t-helmet_offline .tl-dot, .t-camera_offline .tl-dot { background: #5b6673; }
.t-message_sent .tl-dot { background: var(--blue); }
.t-message_received .tl-dot { background: var(--accent); }
.t-alert_acknowledged .tl-dot { background: var(--amber); }
.tl-head { display: flex; justify-content: space-between; gap: 10px; }
.tl-type { font-size: 10px; font-weight: 800; letter-spacing: .12em; color: var(--text); }
.tl-time { font-size: 10px; color: var(--dim); }
.tl-msg { font-size: 12px; color: #a7b4c2; }

.toasts {
  position: fixed; top: 64px; right: 14px; z-index: 3000;
  display: flex; flex-direction: column; gap: 8px; max-width: 340px;
}
.toast {
  padding: 10px 14px; border-radius: 6px; font-size: 12px; font-weight: 600;
  background: var(--panel); border: 1px solid var(--line);
  box-shadow: 0 6px 20px #000a; animation: slideIn .2s ease-out;
}
@keyframes slideIn { from { transform: translateX(24px); opacity: 0; } }
.toast.sos   { border-color: var(--red);   color: var(--red);   background: #23090d; font-size: 13px; }
.toast.warn  { border-color: #55422a; color: var(--amber); }
.toast.ok    { border-color: #1d4a33; color: var(--green); }
.toast.info  { border-color: #1c4653; color: var(--blue); }

.demo-bar {
  position: sticky; bottom: 0; z-index: 1500;
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 10px 14px; background: #141009ee; border-top: 1px solid #55422a;
  backdrop-filter: blur(4px);
}
.demo-label { font-size: 10px; font-weight: 800; letter-spacing: .14em; color: var(--amber); margin-right: auto; }
.demo-gps { font-size: 11px; color: var(--accent); }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #1d2836; border-radius: 4px; }
'''

# ---------------------- firmware/helmet-esp32 ----------------------
FILES["firmware/helmet-esp32/config.h"] = r'''
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
'''

FILES["firmware/helmet-esp32/helmet-esp32.ino"] = r'''
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
'''

FILES["firmware/helmet-esp32/wifi_manager.h"] = r'''
#pragma once
#include <Arduino.h>

namespace WiFiManager {
  void connect(const char* ssid, const char* pass);
  bool isConnected();
  void maintain();      // call every loop - auto-reconnects
  String ip();
  int rssi();
}
'''

FILES["firmware/helmet-esp32/wifi_manager.cpp"] = r'''
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
'''

FILES["firmware/helmet-esp32/firebase_service.h"] = r'''
#pragma once
#include <Arduino.h>

namespace FirebaseService {
  void begin();                       // call after Wi-Fi is up; safe to re-call
  bool isReady();
  void maintain();                    // call every loop: stream + heartbeat
  bool setOnline(bool online);        // helmets/{id} heartbeat
  bool sendSos();                     // push to alerts/
  bool pushEvent(const String& type, const String& message);
  bool popMessage(String& out);       // true when a GS message is queued
}
'''

FILES["firmware/helmet-esp32/firebase_service.cpp"] = r'''
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
'''

FILES["firmware/helmet-esp32/lcd_manager.h"] = r'''
#pragma once
#include <Arduino.h>

namespace LCDManager {
  void begin();
  void showStatus(const String& l1, const String& l2);       // idle screen
  void showMessage(const String& title, const String& body); // priority, auto-expires
  bool isShowingMessage();
  void maintain();   // call every loop - handles scrolling & expiry
}
'''

FILES["firmware/helmet-esp32/lcd_manager.cpp"] = r'''
#include "lcd_manager.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "config.h"

namespace {
  LiquidCrystal_I2C lcd(LCD_I2C_ADDR, LCD_COLS, LCD_ROWS);

  String statusL1, statusL2;
  String msgBody;
  unsigned long msgUntil = 0;
  unsigned long lastScroll = 0;
  int scrollOff = 0;
  bool onMessage = false;

  void writeLine(int row, const String& text) {
    String t = text.substring(0, LCD_COLS);
    while (t.length() < (unsigned)LCD_COLS) t += ' ';
    lcd.setCursor(0, row);
    lcd.print(t);
  }
}

void LCDManager::begin() {
  lcd.init();
  lcd.backlight();
  writeLine(0, "SMART HELMET");
  writeLine(1, "booting...");
}

bool LCDManager::isShowingMessage() { return onMessage && millis() < msgUntil; }

void LCDManager::showStatus(const String& l1, const String& l2) {
  statusL1 = l1;
  statusL2 = l2;
  if (!isShowingMessage()) {
    writeLine(0, l1);
    writeLine(1, l2);
  }
}

void LCDManager::showMessage(const String& title, const String& body) {
  msgBody = body;
  scrollOff = 0;
  msgUntil = millis() + MSG_DISPLAY_MS;
  onMessage = true;
  lastScroll = millis();
  writeLine(0, title);
  writeLine(1, body);
}

void LCDManager::maintain() {
  if (!onMessage) return;

  if (!isShowingMessage()) {           // expired -> restore idle screen
    onMessage = false;
    writeLine(0, statusL1);
    writeLine(1, statusL2);
    return;
  }

  // scroll bodies longer than 16 chars (non-blocking)
  if (msgBody.length() > (unsigned)LCD_COLS && millis() - lastScroll > 350) {
    lastScroll = millis();
    scrollOff++;
    if (scrollOff + LCD_COLS >= (int)msgBody.length() + 2) scrollOff = 0;
    writeLine(1, msgBody.substring(scrollOff, scrollOff + LCD_COLS));
  }
}
'''

FILES["firmware/helmet-esp32/buzzer_manager.h"] = r'''
#pragma once
#include <Arduino.h>

namespace Buzzer {
  void begin();
  void beep(int times, int onMs, int offMs); // non-blocking pattern
  void maintain();                           // call every loop
}
'''

FILES["firmware/helmet-esp32/buzzer_manager.cpp"] = r'''
#include "buzzer_manager.h"
#include <Arduino.h>
#include "config.h"

namespace {
  const int FREQ = 2400;
  bool beeping = false;
  int remain = 0;
  bool toneOn = false;
  unsigned long nextFlip = 0;
  int onMs = 100, offMs = 100;

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  inline void toneStart() { ledcWriteTone(PIN_BUZZER, FREQ); }
  inline void toneStop()  { ledcWriteTone(PIN_BUZZER, 0); }
#else
  inline void toneStart() { ledcWriteTone(0, FREQ); }
  inline void toneStop()  { ledcWriteTone(0, 0); }
#endif
}

void Buzzer::begin() {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_BUZZER, FREQ, 8);   // core 3.x API
#else
  ledcSetup(0, FREQ, 8);             // core 2.x API
  ledcAttachPin(PIN_BUZZER, 0);
#endif
  toneStop();
}

void Buzzer::beep(int times, int onMs_, int offMs_) {
  remain = times * 2;   // on + off per beep
  onMs = onMs_;
  offMs = offMs_;
  beeping = true;
  toneOn = false;
  nextFlip = 0;
}

void Buzzer::maintain() {
  if (!beeping) return;
  unsigned long now = millis();
  if (nextFlip == 0) nextFlip = now;
  if (now < nextFlip) return;

  if (toneOn) {
    toneStop();
    toneOn = false;
    remain--;
    nextFlip = now + offMs;
  } else if (remain > 0) {
    toneStart();
    toneOn = true;
    nextFlip = now + onMs;
  } else {
    beeping = false;
  }
}
'''

FILES["firmware/helmet-esp32/button_manager.h"] = r'''
#pragma once
#include <Arduino.h>

namespace Button {
  void begin();
  bool pressed();  // true exactly once per physical press (debounced)
}
'''

FILES["firmware/helmet-esp32/button_manager.cpp"] = r'''
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
'''

FILES["firmware/helmet-esp32/event_manager.h"] = r'''
#pragma once
#include <Arduino.h>

namespace EventManager {
  void begin();
  void push(const String& type, const String& msg); // queued, flushed to Firebase
  void maintain();                                   // call every loop
}
'''

FILES["firmware/helmet-esp32/event_manager.cpp"] = r'''
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
'''

FILES["firmware/helmet-esp32/README.md"] = r'''
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
'''

# ---------------------- firmware/esp32-cam ----------------------
FILES["firmware/esp32-cam/config.h"] = r'''
#pragma once
// ESP32-CAM configuration - EDIT LOCALLY, never commit credentials

#define CAM_WIFI_SSID "YOUR_WIFI_SSID"
#define CAM_WIFI_PASS "YOUR_WIFI_PASSWORD"

#define CAM_HELMET_ID   "HELMET_01"      // reported by /status
#define CAM_STREAM_PORT 80

#define CAM_FRAME_SIZE   FRAMESIZE_SVGA  // QVGA / VGA / SVGA / HD ...
#define CAM_JPEG_QUALITY 12              // 0-63, lower = better quality
#define CAM_XCLK_MHZ     20
'''

FILES["firmware/esp32-cam/esp32-cam.ino"] = r'''
/*
 * SIH 2026 — Smart Helmet · AI-Thinker ESP32-CAM firmware
 * Endpoints:
 *   /         status page (embedded live view)
 *   /status   JSON {status, helmet, stream}
 *   /capture  single JPEG
 *   /stream   MJPEG stream  <- use this in the Ground Station
 * Prints the stream URL to Serial after connecting.
 */
#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include "config.h"

WebServer server(CAM_STREAM_PORT);

// AI-Thinker pin map
#define PWDN_GPIO_NUM  32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM   0
#define SIOD_GPIO_NUM  26
#define SIOC_GPIO_NUM  27
#define Y9_GPIO_NUM    35
#define Y8_GPIO_NUM    34
#define Y7_GPIO_NUM    39
#define Y6_GPIO_NUM    36
#define Y5_GPIO_NUM    21
#define Y4_GPIO_NUM    19
#define Y3_GPIO_NUM    18
#define Y2_GPIO_NUM     5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM  23
#define PCLK_GPIO_NUM  22

static const char* PART_BOUNDARY = "123456789000000000000987654321";

bool initCamera() {
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0;
  c.ledc_timer   = LEDC_TIMER_0;
  c.pin_d0 = Y2_GPIO_NUM;  c.pin_d1 = Y3_GPIO_NUM;
  c.pin_d2 = Y4_GPIO_NUM;  c.pin_d3 = Y5_GPIO_NUM;
  c.pin_d4 = Y6_GPIO_NUM;  c.pin_d5 = Y7_GPIO_NUM;
  c.pin_d6 = Y8_GPIO_NUM;  c.pin_d7 = Y9_GPIO_NUM;
  c.pin_xclk = XCLK_GPIO_NUM;
  c.pin_pclk = PCLK_GPIO_NUM;
  c.pin_vsync = VSYNC_GPIO_NUM;
  c.pin_href  = HREF_GPIO_NUM;
  c.pin_sccb_sda = SIOD_GPIO_NUM;
  c.pin_sccb_scl = SIOC_GPIO_NUM;
  c.pin_pwdn  = PWDN_GPIO_NUM;
  c.pin_reset = RESET_GPIO_NUM;
  c.xclk_freq_hz = CAM_XCLK_MHZ * 1000000;
  c.pixel_format = PIXFORMAT_JPEG;
  c.grab_mode    = CAMERA_GRAB_LATEST;

  if (psramFound()) {
    c.frame_size   = CAM_FRAME_SIZE;
    c.jpeg_quality = CAM_JPEG_QUALITY;
    c.fb_count     = 2;
    c.fb_location  = CAMERA_FB_IN_PSRAM;
  } else {
    c.frame_size   = FRAMESIZE_QVGA;
    c.jpeg_quality = 14;
    c.fb_count     = 1;
    c.fb_location  = CAMERA_FB_IN_DRAM;
  }
  return esp_camera_init(&c) == ESP_OK;
}

void handleCapture() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) { server.send(500, "text/plain", "capture failed"); return; }
  WiFiClient client = server.client();
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: image/jpeg");
  client.printf("Content-Length: %u\r\n\r\n", fb->len);
  client.write((const char*)fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

void handleStream() {
  WiFiClient client = server.client();
  client.println("HTTP/1.1 200 OK");
  client.printf("Content-Type: multipart/x-mixed-replace;boundary=%s\r\n\r\n", PART_BOUNDARY);

  while (client.connected()) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) { delay(50); continue; }
    client.print(String("\r\n--") + PART_BOUNDARY + "\r\n");
    client.printf("Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", fb->len);
    client.write((const char*)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    if (!client.connected()) break;
  }
}

void handleStatus() {
  String json = "{\"status\":\"online\",\"helmet\":\"" + String(CAM_HELMET_ID) +
                "\",\"stream\":\"http://" + WiFi.localIP().toString() +
                ":" + String(CAM_STREAM_PORT) + "/stream\"}";
  server.send(200, "application/json", json);
}

void handleRoot() {
  String html =
    "<!doctype html><title>ESP32-CAM</title>"
    "<body style='background:#000;color:#3f6;font-family:monospace'>"
    "<h3>ESP32-CAM ready</h3>"
    "<p>Helmet: " + String(CAM_HELMET_ID) + "</p>"
    "<p>Stream URL: http://" + WiFi.localIP().toString() + ":" +
    String(CAM_STREAM_PORT) + "/stream</p>"
    "<img src='/stream' style='max-width:100%'></body>";
  server.send(200, "text/html", html);
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);  // brownout off (weak USB power)
  Serial.begin(115200);
  delay(300);

  pinMode(4, OUTPUT);        // on-board flash LED - keep off
  digitalWrite(4, LOW);

  if (!initCamera()) {
    Serial.println("[CAM] camera init FAILED - check board/power");
    while (true) delay(1000);
  }
  Serial.println("[CAM] camera initialised");

  WiFi.mode(WIFI_STA);
  WiFi.begin(CAM_WIFI_SSID, CAM_WIFI_PASS);
  Serial.print("[WIFI] connecting");
  while (WiFi.status() != WL_CONNECTED) { delay(400); Serial.print('.'); }
  Serial.println();

  server.on("/", HTTP_GET, handleRoot);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/stream", HTTP_GET, handleStream);
  server.begin();

  Serial.println();
  Serial.println("ESP32-CAM ready");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP().toString());
  Serial.print("Stream: http://");
  Serial.print(WiFi.localIP().toString());
  Serial.print(":");
  Serial.print(CAM_STREAM_PORT);
  Serial.println("/stream");
}

void loop() {
  server.handleClient();
}
'''

FILES["firmware/esp32-cam/README.md"] = r'''
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
'''

# ==================== EXECUTION ====================

def write_all() -> int:
    n = 0
    for rel, content in FILES.items():
        p = os.path.join(ROOT, rel)
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
        body = content.strip("\n") + "\n"
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        n += 1
    return n

SKIP_DIRS = {"node_modules", "dist", ".git", "__pycache__", ".vscode"}
SKIP_FILES = {".env", "bootstrap_sih.py"}

def collect(bases):
    out = []
    for base in bases:
        if os.path.isfile(base):
            out.append(base)
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for fn in sorted(files):
                if fn in SKIP_FILES or fn.endswith(".zip"):
                    continue
                out.append(os.path.join(root, fn))
    return out

def make_zip(zip_name, bases):
    path = os.path.join(ROOT, zip_name)
    if os.path.exists(path):
        os.remove(path)
    members = collect(bases)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for m in members:
            zf.write(m, os.path.relpath(m, ROOT).replace(os.sep, "/"))
    names = set(zipfile.ZipFile(path).namelist())
    print(f"[ZIP] {zip_name}: {len(members)} files, {os.path.getsize(path)//1024} KB")
    return names

def run_step(cmd, cwd):
    print(f"\n$ {cmd}")
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd)
        return r.returncode == 0
    except Exception as e:
        print(f"[WARN] could not run: {e}")
        return False

def main():
    print("=" * 60)
    print("SIH 2026 SMART HELMET - bootstrap")
    print("=" * 60)

    n = write_all()
    print(f"[OK] wrote {n} files")

    gs = os.path.join(ROOT, "ground-station")
    have_node = shutil.which("npm") is not None or shutil.which("npm.cmd") is not None
    if have_node:
        print("\n-- npm install (few minutes, please wait) --")
        if run_step("npm install", gs):
            print("\n-- production build (type-check + bundle) --")
            if run_step("npm run build", gs):
                print("[OK] production build PASSED")
            else:
                print("[WARN] build failed - check output above (ZIPs still created)")
        else:
            print("[WARN] npm install failed - ZIPs still created")
    else:
        print("[SKIP] npm not found. Install Node.js from nodejs.org, then run:")
        print("       cd ground-station && npm install && npm run dev")

    complete = make_zip("sih-smart-helmet-complete.zip",
                        ["ground-station", "firmware", "firebase", "docs",
                         "README.md", ".gitignore", "package-zips.sh", "package-zips.ps1"])
    gs_zip = make_zip("ground-station.zip", ["ground-station"])
    fw_zip = make_zip("firmware.zip", ["firmware"])

    checks = {
        "sih-smart-helmet-complete.zip": [
            "ground-station/src/App.tsx", "ground-station/src/styles/global.css",
            "firmware/helmet-esp32/helmet-esp32.ino", "firmware/esp32-cam/esp32-cam.ino",
            "firebase/database.rules.json", "README.md"],
        "ground-station.zip": ["ground-station/package.json", "ground-station/src/main.tsx"],
        "firmware.zip": ["firmware/helmet-esp32/config.h", "firmware/esp32-cam/config.h"],
    }
    zmap = {"sih-smart-helmet-complete.zip": complete,
            "ground-station.zip": gs_zip, "firmware.zip": fw_zip}
    ok = True
    for zname, paths in checks.items():
        for p in paths:
            if p not in zmap[zname]:
                print(f"[FAIL] {p} missing from {zname}")
                ok = False
    print("\n[OK] ZIP content verification PASSED" if ok else "\n[FAIL] ZIP verification FAILED")

    print("\n" + "=" * 60)
    print("DONE. Your 3 ZIP files are now in this folder:")
    for z in ("sih-smart-helmet-complete.zip", "ground-station.zip", "firmware.zip"):
        print("  -", z)
    print("\nTo open the dashboard:")
    print("  cd ground-station")
    print("  npm run dev")
    print("  then open http://localhost:5173 in your browser")
    print("=" * 60)

if __name__ == "__main__":
    sys.exit(main())
# ===== END OF SCRIPT =====