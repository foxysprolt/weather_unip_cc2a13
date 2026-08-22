#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>
#include <DHT.h>

// --- CONFIGURAÇÃO DA VERSÃO DO FIRMWARE ---
const String FIRMWARE_VERSION = "v1.2.1"; // Incremente aqui a cada nova versão (ex: v1.0.1)
const String GITHUB_BIN_URL = "https://github.com/seu-usuario/seu-repositorio/releases/latest/download/firmware.bin";

// --- CREDENCIAIS DE REDE E THINGSPEAK ---
const char* WIFI_SSID = "Ester 2.4G";
const char* WIFI_PASS = "Ester 3600";

const char* CHANNEL_ID = "3465259";
const char* WRITE_API_KEY = "OGC5WGBQU4OU3GJA";
const char* READ_API_KEY = "E6VGVV45AMAC0205";

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastTime = 0;
const unsigned long timerDelay = 15000; // 15 segundos

void executarOTA() {
  Serial.println("🚀 [OTA] Comando de atualização recebido via ThingSpeak!");
  Serial.println("🌐 [OTA] Baixando firmware do GitHub...");

  WiFiClientSecure client;
  client.setInsecure(); // Ignora validação SSL estática do GitHub

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
      // Reseta a flag field4 para 0 no ThingSpeak antes de atualizar
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

  HTTPClient http;
  String url = "https://api.thingspeak.com/update?api_key=" + String(WRITE_API_KEY);
  url += "&field1=" + String(t);
  url += "&field2=" + String(h);
  url += "&field3=" + FIRMWARE_VERSION; // Transmite a versão gravada no chip!

  http.begin(url);
  int httpCode = http.GET();
  if (httpCode == 200) {
    Serial.printf(" [Data] Temp: %.1f °C | Umid: %.0f %% | Versão: %s\n", t, h, FIRMWARE_VERSION.c_str());
  }
  http.end();

  // Verifica se o dashboard acionou o Field 4
  checarComandoOTA();
}

void setup() {
  Serial.begin(115200);
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
  if ((millis() - lastTime) > timerDelay) {
    if (WiFi.status() == WL_CONNECTED) {
      enviarDadosECheck();
    }
    lastTime = millis();
  }
}