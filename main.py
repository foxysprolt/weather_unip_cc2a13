import dht
from machine import ADC, I2C, Pin
import network
import ssd1306
import time
import urequests

# ==========================================
# 1. CONFIGURACOES DA REDE E API
# ==========================================
WIFI_SSID = "Ester 2.4G"
WIFI_PASS = "Ester3600"
WRITE_API_KEY = "OGC5WGBQU4OU3GJA"

# ==========================================
# 2. SENSORES LIGADOS NO MOMENTO
# ==========================================
USAR_TEMPERATURA = True
USAR_UMIDADE = True
USAR_LUZ = True
USAR_GAS = False
USAR_PRESSAO = False

# ==========================================
# 3. CONFIGURACAO DOS PINOS E HARDWARE
# ==========================================
dht_sensor = dht.DHT11(Pin(4))
ldr_sensor = Pin(15, Pin.IN)
gas_sensor = ADC(Pin(2))
gas_sensor.atten(ADC.ATTN_11DB)

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
display = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

temp = 0.0
umid = 0.0
luz = 0
gas = 0
pressao = 1013.0
latitude = 0.0
longitude = 0.0
cidade = ""

# ==========================================
# 4. CONECTAR AO WI-FI
# ==========================================
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1)
wlan.active(True)
time.sleep(1)

print("Conectando ao Wi-Fi...")
try:
    wlan.connect(WIFI_SSID, WIFI_PASS)
except OSError as e:
    print("Erro ao iniciar conexao Wi-Fi:", e)

while not wlan.isconnected():
    time.sleep(0.5)
    print(".")

print("Wi-Fi conectado com sucesso!")
print("IP obtido:", wlan.ifconfig()[0])


def buscar_localizacao_ip():
    global latitude, longitude, cidade

    enderecos = [
        "https://ipapi.co/json/",
        "http://ip-api.com/json/?fields=status,city,lat,lon"
    ]

    for endereco in enderecos:
        try:
            resposta = urequests.get(endereco)
            dados = resposta.json()
            resposta.close()

            latitude = float(dados.get("latitude", dados.get("lat", 0)))
            longitude = float(dados.get("longitude", dados.get("lon", 0)))
            cidade = dados.get("city", "")

            if latitude != 0 and longitude != 0:
                print("Localizacao aproximada:", cidade)
                print("Latitude:", latitude, "Longitude:", longitude)
                return
        except Exception as e:
            print("Erro na consulta de localizacao:", e)

    print("Nao foi possivel obter a localizacao pelo IP")


buscar_localizacao_ip()


def mostrar_na_tela(titulo, valor):
    display.fill(0)
    display.rect(0, 0, 128, 64, 1)
    display.fill_rect(0, 0, 128, 14, 1)
    display.text(titulo, 8, 3, 0)
    display.text(str(valor), 20, 32, 1)
    display.show()


while True:
    if USAR_TEMPERATURA or USAR_UMIDADE:
        try:
            dht_sensor.measure()
            if USAR_TEMPERATURA:
                temp = dht_sensor.temperature()
            if USAR_UMIDADE:
                umid = dht_sensor.humidity()
        except Exception as e:
            print("Erro ao ler o DHT11:", e)

    if USAR_LUZ:
        luz = 4095 if ldr_sensor.value() == 0 else 0

    if USAR_GAS:
        gas = gas_sensor.read()

    if USAR_PRESSAO:
        pressao = 1013.0

    if USAR_TEMPERATURA:
        mostrar_na_tela("TEMPERATURA", "{:.1f} C".format(temp))
        time.sleep(3)

    if USAR_UMIDADE:
        mostrar_na_tela("UMIDADE DO AR", "{} %".format(int(umid)))
        time.sleep(3)

    if USAR_LUZ:
        status_luz = "DIA" if luz > 2000 else "NOITE"
        mostrar_na_tela("LUMINOSIDADE", status_luz)
        time.sleep(3)

    if USAR_GAS:
        mostrar_na_tela("GAS / FUMACA", gas)
        time.sleep(3)

    if USAR_PRESSAO:
        mostrar_na_tela("PRESSAO ATM", "{} hPa".format(int(pressao)))
        time.sleep(3)

    print("Enviando dados para o ThingSpeak...")
    url = "https://api.thingspeak.com/update?api_key={}".format(WRITE_API_KEY)

    if latitude != 0 and longitude != 0:
        url += "&lat={}&long={}".format(latitude, longitude)

    if USAR_TEMPERATURA:
        url += "&field1={}".format(temp)
    if USAR_UMIDADE:
        url += "&field2={}".format(umid)
    if USAR_LUZ:
        url += "&field3={}".format(luz)
    if USAR_GAS:
        url += "&field6={}".format(gas)
    if USAR_PRESSAO:
        url += "&field7={}".format(pressao)

    try:
        resposta = urequests.get(url)
        print("Dados enviados! Resposta da API:", resposta.status_code)
        resposta.close()
    except Exception as e:
        print("Erro no envio para a API:", e)
