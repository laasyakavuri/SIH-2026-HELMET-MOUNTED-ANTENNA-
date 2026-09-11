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
