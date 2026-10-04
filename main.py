import dht
from machine import ADC, I2C, Pin
import network
import ssd1306
import time
import urequests

# ==========================================
# ESTACAO METEOROLOGICA - VERSAO PRINCIPAL
# ==========================================
WIFI_SSID = "Ester 2.4G"
WIFI_PASS = "Ester3600"
WRITE_API_KEY = "OGC5WGBQU4OU3GJA"

# Sensores ativos nesta montagem
USAR_TEMPERATURA = True
USAR_UMIDADE = True
USAR_LUZ = True
USAR_GAS = True
USAR_PRESSAO = False

# Pinos usados
dht_sensor = dht.DHT11(Pin(4))
ldr_sensor = Pin(15, Pin.IN)
gas_sensor = ADC(Pin(34))
gas_sensor.atten(ADC.ATTN_11DB)

# OLED e BMP280 podem compartilhar este barramento I2C
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

wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1)
wlan.active(True)
time.sleep(1)


def conectar_wifi():
    if wlan.isconnected():
        return True

    print("Conectando ao Wi-Fi...")
    try:
        wlan.connect(WIFI_SSID, WIFI_PASS)
    except OSError as e:
        print("Erro ao iniciar Wi-Fi:", e)
        return False

    tentativas = 20
    while not wlan.isconnected() and tentativas > 0:
        time.sleep(0.5)
        print(".")
        tentativas -= 1

    return wlan.isconnected()


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
                print("Localizacao:", cidade)
                print("Latitude:", latitude, "Longitude:", longitude)
                return
        except Exception as e:
            print("Erro na localizacao:", e)

    print("Localizacao por IP indisponivel")


def ler_dht():
    # O DHT11 pode falhar ocasionalmente; fazemos ate tres tentativas.
    for tentativa in range(3):
        try:
            dht_sensor.measure()
            return dht_sensor.temperature(), dht_sensor.humidity()
        except Exception as e:
            print("Erro ao ler DHT11, tentativa", tentativa + 1, e)
            time.sleep(2)

    return 0.0, 0.0


def mostrar_na_tela(titulo, valor):
    display.fill(0)
    display.rect(0, 0, 128, 64, 1)
    display.fill_rect(0, 0, 128, 14, 1)
    display.text(titulo, 8, 3, 0)
    display.text(str(valor), 20, 32, 1)
    display.show()


def enviar_dados():
    if not conectar_wifi():
        print("Dados nao enviados: Wi-Fi sem conexao")
        return

    url = "https://api.thingspeak.com/update?api_key={}".format(WRITE_API_KEY)

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
    if latitude != 0 and longitude != 0:
        url += "&lat={}&long={}".format(latitude, longitude)

    try:
        resposta = urequests.get(url)
        print("Dados enviados. Resposta da API:", resposta.status_code)
        resposta.close()
    except Exception as e:
        print("Erro ao enviar dados:", e)


if conectar_wifi():
    buscar_localizacao_ip()

while True:
    if USAR_TEMPERATURA or USAR_UMIDADE:
        temp, umid = ler_dht()

    if USAR_LUZ:
        luz = 4095 if ldr_sensor.value() == 0 else 0

    if USAR_GAS:
        gas = gas_sensor.read()

    print("Temperatura:", temp)
    print("Umidade:", umid)
    print("Luz:", luz)
    print("Gas:", gas)

    if USAR_TEMPERATURA:
        mostrar_na_tela("TEMPERATURA", "{:.1f} C".format(temp))
        time.sleep(2)
    if USAR_UMIDADE:
        mostrar_na_tela("UMIDADE", "{} %".format(int(umid)))
        time.sleep(2)
    if USAR_LUZ:
        mostrar_na_tela("LUZ", "DIA" if luz > 2000 else "NOITE")
        time.sleep(2)
    if USAR_GAS:
        mostrar_na_tela("GAS MQ-2", gas)
        time.sleep(2)

    enviar_dados()
    time.sleep(16)
