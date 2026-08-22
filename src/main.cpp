#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- DISPLAY OLED ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- VERSÃO DO FIRMWARE ---
const String FIRMWARE_VERSION = "v1.2.6"; 
const String GITHUB_BIN_URL = "https://github.com/foxysprolt/weather_unip_cc2a13/releases/latest/download/firmware.bin";

// --- CREDENCIAIS ---
const char* WIFI_SSID = "Ester 2.4G";
const char* WIFI_PASS = "Ester 3600";

const char* CHANNEL_ID = "3465259";
const char* WRITE_API_KEY = "OGC5WGBQU4OU3GJA";
const char* READ_API_KEY = "E6VGVV45AMAC0205";

// --- PINOS ---
#define DHTPIN 4
#define DHTTYPE DHT11
#define LDR_PIN 15

DHT dht(DHTPIN, DHTTYPE);

unsigned long lastTime = 0;
const unsigned long timerDelay = 15000;
unsigned long ultimaTrocaTela = 0;
int telaAtual = 0;

float tempG = 0;
float umidG = 0;
int luzG = 0;

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
      display.print(tempG, 1);
      display.setTextSize(1);
      display.print(" C");
      break;

    case 1:
      desenharHeader("UMIDADE DO AR");
      display.setTextSize(3);
      display.setCursor(22, 22);
      display.print((int)umidG);
      display.print(" %");
      break;

    case 2:
      desenharHeader("LUMINOSIDADE (LDR)");
      display.setTextSize(2);
      display.setCursor(18, 25);
      if (luzG > 2000) display.print("DIA ☀️");
      else display.print("NOITE 🌙");
      break;
  }
  display.display();
}

void executarOTA() {
  Serial.println("🚀 [OTA] Comando de atualização recebido via ThingSpeak!");
  Serial.println("🌐 [OTA] Baixando firmware do GitHub...");

  display.clearDisplay();
  desenharHeader("ATUALIZANDO OTA");
  display.setTextSize(1);
  display.setCursor(10, 30);
  display.print("Baixando Firmware...");
  display.display();

  WiFiClientSecure client;
  client.setInsecure(); 

  t_httpUpdate_return ret = httpUpdate.update(client, GITHUB_BIN_URL);

  switch (ret) {
    case HTTP_UPDATE_FAILED:
      Serial.printf("❌ [OTA] Falha: (%d): %s\n", httpUpdate.getLastError(), httpUpdate.getLastErrorString().c_str());
      break;
    case HTTP_UPDATE_NO_UPDATES:
      Serial.println("⚠️ [OTA] Nenhuma atualização pendente no servidor.");
      break;
    case HTTP_UPDATE_OK:
      Serial.println("✅ [OTA] Firmware atualizado com sucesso! Reiniciando...");
      ESP.restart();
      break;
  }
}

void checarComandoOTA() {
  HTTPClient http;
  String url = "https://api.thingspeak.com/channels/" + String(CHANNEL_ID) + "/fields/4/last.json?api_key=" + String(READ_API_KEY);
  
  http.begin(url);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    if (payload.indexOf("\"field4\":\"1\"") != -1) {
      // Reseta a flag field4 para 0 no ThingSpeak
      HTTPClient resetHttp;
      String resetUrl = "https://api.thingspeak.com/update?api_key=" + String(WRITE_API_KEY) + "&field4=0";
      resetHttp.begin(resetUrl);
      resetHttp.GET();
      resetHttp.end();

      executarOTA();
    }
  }
  http.end();
}

void enviarDadosECheck() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    Serial.println("Falha ao ler o sensor DHT!");
    return;
  }

  tempG = t;
  umidG = h;

  int leituraDigital = digitalRead(LDR_PIN);
  luzG = (leituraDigital == LOW) ? 4095 : 0;

  HTTPClient http;
  String url = "https://api.thingspeak.com/update?api_key=" + String(WRITE_API_KEY);
  url += "&field1=" + String(t);
  url += "&field2=" + String(h);
  url += "&field3=" + String(luzG);             // Field 3: LDR
  url += "&field5=" + FIRMWARE_VERSION;         // Field 5: Versão para o Cockpit

  http.begin(url);
  int httpCode = http.GET();
  if (httpCode == 200) {
    Serial.printf(" [Data] Temp: %.1f °C | Umid: %.0f %% | LDR: %d | Ver: %s\n", t, h, luzG, FIRMWARE_VERSION.c_str());
  }
  http.end();

  checarComandoOTA();
}

void setup() {
  Serial.begin(115200);
  pinMode(LDR_PIN, INPUT);

  Wire.begin(21, 22);
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    display.clearDisplay();
  }

  dht.begin();

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Conectado!");
}

void loop() {
  atualizarOLED();

  if ((millis() - lastTime) > timerDelay) {
    if (WiFi.status() == WL_CONNECTED) {
      enviarDadosECheck();
    }
    lastTime = millis();
  }
}