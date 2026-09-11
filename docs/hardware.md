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
