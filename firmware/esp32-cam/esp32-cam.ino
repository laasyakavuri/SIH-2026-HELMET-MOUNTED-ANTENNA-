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
