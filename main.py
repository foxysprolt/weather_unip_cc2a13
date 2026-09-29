import dht
from machine import ADC, I2C, Pin
import network
import weather_unip_cc2a13.ssd1306 as ssd1306
import time
import urequests

# ==========================================
# 1. CONFIGURAÇÕES DA REDE E API
# ==========================================
WIFI_SSID = "Ester 2.4G"
WIFI_PASS = "Ester3600"
WRITE_API_KEY = "OGC5WGBQU4OU3GJA"

# ==========================================
# 2. SENSORES LIGADOS NO MOMENTO
# (Troque para True quando religar na energia)
# ==========================================
USAR_TEMPERATURA = True
USAR_UMIDADE = True
USAR_LUZ = True
USAR_GAS = False
USAR_PRESSAO = False

# ==========================================
# 3. CONFIGURAÇÃO DOS PINOS E HARDWARE
# ==========================================
# Sensores
dht_sensor = dht.DHT11(Pin(4))  # Pino D4
ldr_sensor = Pin(15, Pin.IN)  # Pino D15
gas_sensor = ADC(Pin(2))  # Pino D2
gas_sensor.atten(ADC.ATTN_11DB)

# Tela OLED (I2C)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
display = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Variáveis para guardar as leituras
temp = 0.0
umid = 0.0
luz = 0
gas = 0
pressao = 1013.0  # Valor padrao de pressao (hPa)

# ==========================================
# 4. CONECTAR AO WI-FI
# ==========================================
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print("Conectando ao Wi-Fi...")
wlan.connect(WIFI_SSID, WIFI_PASS)

while not wlan.isconnected():
    time.sleep(0.5)
    print(".")

print("Wi-Fi Conectado com sucesso!")
print("IP obtido:", wlan.ifconfig()[0])


# ==========================================
# 5. FUNÇÃO PARA DESENHAR NA TELA OLED
# ==========================================
def mostrar_na_tela(titulo, valor):
    display.fill(0)  # Limpa a tela
    display.rect(0, 0, 128, 64, 1)  # Borda externa
    display.fill_rect(0, 0, 128, 14, 1)  # Barra do titulo
    display.text(titulo, 8, 3, 0)  # Titulo em preto
    display.text(str(valor), 20, 32, 1)  # Valor no meio
    display.show()


# ==========================================
# 6. LOOP PRINCIPAL DO PROGRAMA
# ==========================================
while True:
    # --------------------------------------
    # A) LEITURA DOS SENSORES
    # --------------------------------------
    if USAR_TEMPERATURA or USAR_UMIDADE:
        try:
            dht_sensor.measure()
            if USAR_TEMPERATURA:
                temp = dht_sensor.temperature()
            if USAR_UMIDADE:
                umid = dht_sensor.humidity()
        except Exception:
            print("Erro ao ler o DHT11")

    if USAR_LUZ:
        luz = 4095 if ldr_sensor.value() == 0 else 0

    if USAR_GAS:
        gas = gas_sensor.read()

    if USAR_PRESSAO:
        pressao = 1013.0  # Aqui entra a leitura do BMP280 quando instalado

    # --------------------------------------
    # B) MOSTRAR NO OLED (Apenas os ATIVOS)
    # --------------------------------------
    if USAR_TEMPERATURA:
        mostrar_na_tela("TEMPERATURA", f"{temp:.1f} C")
        time.sleep(3)

    if USAR_UMIDADE:
        mostrar_na_tela("UMIDADE DO AR", f"{int(umid)} %")
        time.sleep(3)

    if USAR_LUZ:
        status_luz = "DIA" if luz > 2000 else "NOITE"
        mostrar_na_tela("LUMINOSIDADE", status_luz)
        time.sleep(3)

    if USAR_GAS:
        mostrar_na_tela("GAS / FUMACA", gas)
        time.sleep(3)

    if USAR_PRESSAO:
        mostrar_na_tela("PRESSAO ATM", f"{int(pressao)} hPa")
        time.sleep(3)

    # --------------------------------------
    # C) ENVIAR DADOS PARA O THINGSPEAK
    # --------------------------------------
    print("Enviando dados para o ThingSpeak...")

    url = f"https://api.thingspeak.com/update?api_key={WRITE_API_KEY}"

    if USAR_TEMPERATURA:
        url += f"&field1={temp}"
    if USAR_UMIDADE:
        url += f"&field2={umid}"
    if USAR_LUZ:
        url += f"&field3={luz}"
    if USAR_GAS:
        url += f"&field6={gas}"
    if USAR_PRESSAO:
        url += f"&field7={pressao}"

    try:
        resposta = urequests.get(url)
        print("Dados enviados! Resposta da API:", resposta.status_code)
        resposta.close()
    except Exception as e:
        print("Erro no envio para a API:", e)
        