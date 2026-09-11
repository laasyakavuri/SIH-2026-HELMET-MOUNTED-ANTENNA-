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
