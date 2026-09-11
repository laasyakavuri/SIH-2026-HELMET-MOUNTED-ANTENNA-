#pragma once
// ESP32-CAM configuration - EDIT LOCALLY, never commit credentials

#define CAM_WIFI_SSID "YOUR_WIFI_SSID"
#define CAM_WIFI_PASS "YOUR_WIFI_PASSWORD"

#define CAM_HELMET_ID   "HELMET_01"      // reported by /status
#define CAM_STREAM_PORT 80

#define CAM_FRAME_SIZE   FRAMESIZE_SVGA  // QVGA / VGA / SVGA / HD ...
#define CAM_JPEG_QUALITY 12              // 0-63, lower = better quality
#define CAM_XCLK_MHZ     20
