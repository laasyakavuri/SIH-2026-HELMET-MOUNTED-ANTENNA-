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
