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
