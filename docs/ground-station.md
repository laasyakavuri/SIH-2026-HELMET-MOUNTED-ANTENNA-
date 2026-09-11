# Ground Station

Stack: React 18, TypeScript, Vite 5, Leaflet/react-leaflet, Firebase JS SDK.

Layout: header (mode/firebase/online count/clock) - left (fleet list, SOS
panel) - center (live map + 2x2 CCTV grid, click to enlarge) - right
(details, messaging, timeline). Bottom MOCK demo bar in demo mode. Toasts
top-right. Responsive to mobile.

Key modules: services/dataService.ts (interface + REAL/MOCK switch),
firebase/config.ts (env parsing, camera URLs), hooks/useStation.ts,
utils/camera.ts (REAL/MOCK/OFFLINE resolution).
