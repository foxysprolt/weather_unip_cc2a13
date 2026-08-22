#include <Arduino.h>
#include <WiFi.h>
#include "ThingSpeak.h"
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- DISPLAY OLED ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- CONFIGURAÇÕES DE REDE ---
const char* WIFI_SSID = "Ester 2.4G";
const char* WIFI_PASS = "Ester3600";

// --- CONFIGURAÇÕES THINGSPEAK ---
unsigned long CHANNEL_ID = 3465259;
const char* WRITE_API_KEY = "OGC5WGBQU4OU3GJA";

// --- PINOS ---
#define DHTPIN 4       // DHT11
#define DHTTYPE DHT11
#define LDR_PIN 15     // Pino DO do módulo LDR

DHT dht(DHTPIN, DHTTYPE);
WiFiClient client;

// Variáveis Globais
float temp = 0;
float umid = 0;
int luz = 0;
unsigned long ultimoEnvioThingSpeak = 0;
unsigned long ultimaTrocaTela = 0;
int telaAtual = 0;

void desenharHeader(const char* titulo) {
  display.clearDisplay();
  display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
  display.fillRect(0, 0, 128, 14, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK);
  display.setTextSize(1);
  display.setCursor(8, 3);
  display.println(titulo);
  display.setTextColor(SSD1306_WHITE);
}

void atualizarOLED() {
  if (millis() - ultimaTrocaTela > 3000) {
    telaAtual = (telaAtual + 1) % 3;
    ultimaTrocaTela = millis();
  }

  switch (telaAtual) {
    case 0:
      desenharHeader("TEMPERATURA (DHT11)");
      display.setTextSize(3);
      display.setCursor(12, 22);
      display.print(temp, 1);
      display.setTextSize(1);
      display.print(" C");
      break;

    case 1:
      desenharHeader("UMIDADE DO AR");
      display.setTextSize(3);
      display.setCursor(22, 22);
      display.print((int)umid);
      display.print(" %");
      break;

    case 2:
      desenharHeader("STATUS DE LUZ (LDR)");
      display.setTextSize(2);
      display.setCursor(18, 25);
      if (luz > 2000) display.print("DIA ☀️");
      else display.print("NOITE 🌙");
      break;
  }
  display.display();
}

void setup() {
  Serial.begin(115200);
  pinMode(LDR_PIN, INPUT);

  Wire.begin(21, 22);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    for (;;);
  }

  dht.begin();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  ThingSpeak.begin(client);
}

void loop() {
  float t = dht.readTemperature();
  float u = dht.readHumidity();

  if (!isnan(t) && !isnan(u)) {
    temp = t;
    umid = u;
  }

  // --- LEITURA DO LDR DE FÁBRICA (INVERTIDA) ---
  // LOW (0) = Bateu Luz no Módulo -> Envia 4095 (Ativa Modo Claro na Web)
  // HIGH (1) = Escuro -> Envia 0 (Ativa Modo Escuro na Web)
  int leituraDigital = digitalRead(LDR_PIN);
  luz = (leituraDigital == LOW) ? 4095 : 0;

  atualizarOLED();

  if (millis() - ultimoEnvioThingSpeak > 15000) {
    ThingSpeak.setField(1, temp);
    ThingSpeak.setField(2, umid);
    ThingSpeak.setField(3, luz);
    ThingSpeak.writeFields(CHANNEL_ID, WRITE_API_KEY);
    ultimoEnvioThingSpeak = millis();
  }
}