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
