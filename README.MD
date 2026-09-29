# 🌤️ Estação Meteorológica Inteligente IoT com ESP32

> **Projeto Acadêmico** | Engenharia / Ciência da Computação
> **Linguagem:** MicroPython
> **Plataforma Cloud:** ThingSpeak API
> **Interface:** Web Dashboard (GitHub Pages) + Display OLED Local

---

## 📋 Sumário

1. [Visão Geral do Projeto](#-visão-geral-do-projeto)
2. [Arquitetura do Sistema](#-arquitetura-do-sistema)
3. [Hardware e Lista de Componentes](#-hardware-e-lista-de-componentes)
4. [Mapeamento de Pinos (Pinagem)](#-mapeamento-de-pinos-pinagem)
5. [Funcionamento do Código (Firmware)](#-funcionamento-do-código-firmware)
6. [Integração Cloud (API ThingSpeak)](#-integração-cloud-api-thingspeak)
7. [Interface Web (GitHub Pages)](#-interface-web-github-pages)
8. [Como Executar o Projeto](#-como-executar-o-projeto)
9. [Solução de Problemas (Troubleshooting)](#-solução-de-problemas-troubleshooting)

---

## 📌 Visão Geral do Projeto

Este projeto consiste no desenvolvimento de uma **estação meteorológica inteligente baseada em IoT**, utilizando um microcontrolador **ESP32** programado em **MicroPython**.

O sistema realiza a coleta de dados ambientais através de diferentes sensores, processa as informações localmente, apresenta as métricas em um display OLED e envia periodicamente os dados para a nuvem por meio de requisições HTTP.

Os dados armazenados no **ThingSpeak** podem ser posteriormente consultados por uma interface web hospedada no **GitHub Pages**.

### 🎯 Objetivos Principais

* **Coleta multissensorial:** medição de temperatura, umidade, luminosidade, gás/fumaça e pressão atmosférica.
* **Processamento local:** leitura e tratamento dos dados diretamente no ESP32.
* **Tolerância a falhas:** possibilidade de ativar ou desativar sensores individualmente por meio de variáveis booleanas.
* **Monitoramento local:** visualização das informações através de um display OLED.
* **Monitoramento remoto:** envio dos dados para a plataforma ThingSpeak utilizando conexão Wi-Fi.
* **Interface web:** apresentação dos dados em um dashboard hospedado no GitHub Pages.
* **Interface adaptativa:** alteração do tema visual do dashboard de acordo com a luminosidade detectada pelo sensor LDR.

---

## 🏗️ Arquitetura do Sistema

```text
                    ┌───────────────────────────┐
                    │    SENSORES AMBIENTAIS    │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
          ▼                       ▼                        ▼
   ┌────────────┐          ┌────────────┐          ┌────────────┐
   │   DHT11    │          │    LDR     │          │    MQ-2    │
   │ Temp./Umid.│          │Luminosidade│          │ Gás/Fumaça │
   │  GPIO 4    │          │  GPIO 15   │          │   GPIO 2   │
   └──────┬─────┘          └──────┬─────┘          └──────┬─────┘
          │                       │                        │
          └───────────────────────┼────────────────────────┘
                                  │
                                  ▼
                        ┌───────────────────┐
                        │       ESP32       │
                        │    MicroPython    │
                        │                   │
                        │ Processamento     │
                        │ Wi-Fi             │
                        │ HTTP / REST       │
                        └─────────┬─────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
                 ▼                                 ▼
        ┌─────────────────┐              ┌──────────────────┐
        │ Display OLED    │              │  ThingSpeak API  │
        │ SSD1306 128x64  │              │      Cloud       │
        │      I2C        │              └────────┬─────────┘
        └─────────────────┘                       │
                                                  ▼
                                      ┌─────────────────────┐
                                      │    Web Dashboard    │
                                      │    GitHub Pages     │
                                      └─────────────────────┘
```

### Fluxo de Funcionamento

```text
Sensores
   ↓
ESP32
   ↓
Leitura e processamento
   ↓
Display OLED
   ↓
Wi-Fi
   ↓
ThingSpeak
   ↓
Web Dashboard
```

---

## 🧪 Hardware e Lista de Componentes

| Componente                    | Modelo / Especificação          | Qtd. | Função no Sistema                         |
| ----------------------------- | ------------------------------- | ---: | ----------------------------------------- |
| Microcontrolador              | ESP32 DevKit v1 — 30 pinos      |    1 | Processamento e conectividade Wi-Fi       |
| Display Local                 | OLED 0.96" SSD1306 — 128x64 I2C |    1 | Exibição local das métricas               |
| Sensor de Temperatura/Umidade | DHT11                           |    1 | Medição de temperatura e umidade relativa |
| Sensor de Luz                 | LDR — módulo digital/analógico  |    1 | Detecção da iluminação ambiente           |
| Sensor de Gás                 | MQ-2 / MQ-135                   |    1 | Monitoramento de gás e fumaça             |
| Sensor de Pressão             | BMP280                          |    1 | Medição da pressão atmosférica            |
| Fonte de Alimentação          | Cabo Micro-USB 5V               |    1 | Alimentação e comunicação serial          |

> **Observação:** os sensores MQ-2/MQ-135 e BMP280 possuem suporte no código e podem ser ativados conforme a montagem física do projeto.

---

## 🔌 Mapeamento de Pinos (Pinagem)

| Componente   | Pino do Módulo | Pino no ESP32     | Tipo de Sinal   | Observações                               |
| ------------ | -------------- | ----------------- | --------------- | ----------------------------------------- |
| OLED SSD1306 | SDA / SCL      | GPIO 21 / GPIO 22 | Digital — I2C   | Endereço `0x3C`, 400 kHz                  |
| BMP280       | SDA / SCL      | GPIO 21 / GPIO 22 | Digital — I2C   | Compartilha o barramento I2C com o OLED   |
| DHT11        | DATA / OUT     | GPIO 4            | Digital         | Leitura de temperatura e umidade          |
| LDR          | DO             | GPIO 15           | Digital         | Retorna LOW quando detecta luz suficiente |
| MQ-2         | AO             | GPIO 2            | Analógico — ADC | Entrada de 0 V a 3,3 V                    |

### Barramento I2C

O OLED SSD1306 e o BMP280 utilizam o mesmo barramento I2C:

```text
ESP32
 ├── GPIO 21 ── SDA ──┬── OLED SSD1306
 │                    └── BMP280
 │
 └── GPIO 22 ── SCL ──┬── OLED SSD1306
                      └── BMP280
```

---

## 📜 Funcionamento do Código (Firmware)

O firmware principal é desenvolvido em **MicroPython** e possui uma estrutura sequencial e modular, adequada para fins acadêmicos.

### 1. Ativação Seletiva de Hardware

Os sensores podem ser ativados ou desativados por meio de variáveis booleanas:

```python
USAR_TEMPERATURA = True
USAR_UMIDADE     = True
USAR_LUZ         = True
USAR_GAS         = False
USAR_PRESSAO     = False
```

Isso permite executar o firmware mesmo quando determinados sensores não estão conectados fisicamente.

Por exemplo:

```python
USAR_GAS = True
```

pode ser utilizado quando o sensor de gás estiver conectado e configurado.

---

### 2. Conexão Wi-Fi

O ESP32 inicializa sua interface de rede utilizando o módulo `network` do MicroPython.

O firmware aguarda o estabelecimento da conexão antes de iniciar as operações que dependem da Internet.

```text
ESP32
  ↓
Inicialização Wi-Fi
  ↓
Conexão com a rede
  ↓
Internet disponível
  ↓
Comunicação com ThingSpeak
```

---

### 3. Leitura dos Sensores

O firmware realiza a leitura dos sensores habilitados:

* DHT11 → temperatura e umidade;
* LDR → luminosidade;
* MQ-2/MQ-135 → leitura analógica de gás/fumaça;
* BMP280 → pressão atmosférica.

Os sensores opcionais podem permanecer desativados por meio das flags de configuração.

---

### 4. Exibição no OLED

A função `mostrar_na_tela()` apresenta as informações no display OLED.

A interface alterna as informações periodicamente, utilizando:

```python
time.sleep(3)
```

O objetivo é permitir que diferentes métricas sejam exibidas em uma tela de apenas `128x64` pixels.

---

### 5. Envio dos Dados para a Cloud

Após a coleta, os dados são enviados para o ThingSpeak através de requisições HTTP GET.

O firmware utiliza a biblioteca:

```python
urequests
```

para realizar a comunicação com a API.

---

## ☁️ Integração Cloud — ThingSpeak API

O **ThingSpeak** é utilizado como plataforma de armazenamento e visualização dos dados enviados pelo ESP32.

O ESP32 realiza requisições HTTP para atualizar os campos configurados no canal.

### Mapeamento dos Campos

| Campo    | Dado Transmitido       | Unidade / Formato           |
| -------- | ---------------------- | --------------------------- |
| `field1` | Temperatura ambiente   | °C                          |
| `field2` | Umidade relativa do ar | %                           |
| `field3` | Luminosidade           | Valor bruto / estado do LDR |
| `field6` | Gás / fumaça           | Leitura ADC                 |
| `field7` | Pressão atmosférica    | hPa                         |

### Fluxo de Dados

```text
Sensor
   ↓
ESP32
   ↓
Leitura
   ↓
Processamento
   ↓
HTTP GET
   ↓
ThingSpeak API
   ↓
Dados armazenados
   ↓
Dashboard Web
```

---

## 🌐 Interface Web — GitHub Pages

A interface web do projeto é composta por um arquivo:

```text
index.html
```

O arquivo é hospedado no **GitHub Pages** e consulta os dados disponibilizados pelo ThingSpeak.

### Recursos da Interface

#### 📊 Consumo de Dados em Tempo Real

O dashboard utiliza requisições assíncronas `fetch()` para consultar os dados do ThingSpeak periodicamente.

O intervalo configurado é de:

```text
15 segundos
```

---

#### 🌙 Alternância de Tema

A interface pode alterar seu tema visual de acordo com a luminosidade registrada pelo sensor LDR.

```text
Luminosidade
     ↓
ThingSpeak
     ↓
Dashboard
     ↓
Interpretação do field3
     ↓
Modo Claro / Modo Escuro
```

---

#### 💧 Indicadores Visuais

O dashboard apresenta indicadores gráficos para facilitar a interpretação dos dados.

Entre eles:

* nível visual para representar a umidade;
* indicadores de temperatura;
* informação de luminosidade;
* monitoramento da pressão atmosférica;
* alerta visual para detecção de gás/fumaça.

---

## 🚀 Como Executar o Projeto

### 1. Preparar o ESP32

Conecte o ESP32 ao computador através do cabo USB.

Verifique qual porta COM foi atribuída ao dispositivo.

No exemplo abaixo, a porta utilizada é:

```text
COM7
```

> A porta pode ser diferente no seu computador.

---

### 2. Gravar o Firmware MicroPython

Caso seja necessário instalar o firmware MicroPython no ESP32:

```bash
python -m esptool --chip esp32 --port COM7 erase-flash
```

Depois:

```bash
python -m esptool --chip esp32 --port COM7 write_flash -z 0x1000 firmware.bin
```

Substitua `COM7` pela porta correta do seu ESP32.

---

### 3. Estrutura do Projeto no ESP32

Os principais arquivos utilizados no dispositivo são:

```text
projeto/
├── boot.py
├── main.py
└── ssd1306.py
```

#### `boot.py`

Arquivo responsável pelas configurações iniciais executadas durante o boot do MicroPython.

#### `main.py`

Contém a lógica principal da estação meteorológica:

* conexão Wi-Fi;
* leitura dos sensores;
* processamento dos dados;
* atualização do OLED;
* envio para o ThingSpeak.

#### `ssd1306.py`

Driver utilizado para comunicação com o display OLED SSD1306.

---

### 4. Upload pelo VS Code

Com o **MicroPico** instalado:

1. Abra a pasta do projeto no VS Code.
2. Conecte o ESP32 via USB.
3. Certifique-se de que `boot.py`, `main.py` e `ssd1306.py` estão na pasta do projeto.
4. Abra a Paleta de Comandos:

```text
Ctrl + Shift + P
```

5. Execute:

```text
MicroPico: Upload project to board
```

---

### 5. Configurar o ThingSpeak

Antes de executar o firmware, configure o canal do ThingSpeak de acordo com o mapeamento utilizado pelo código:

```text
Field 1 → Temperatura
Field 2 → Umidade
Field 3 → Luminosidade
Field 6 → Gás/Fumaça
Field 7 → Pressão
```

Configure também no firmware as credenciais necessárias para o acesso à rede Wi-Fi e à API.

> **Importante:** não publique chaves de API, senhas de Wi-Fi ou outras credenciais diretamente no GitHub.

---

### 6. Publicar o Dashboard no GitHub Pages

Para publicar a interface:

1. Faça o commit do arquivo `index.html`.
2. Envie o arquivo para o repositório:

```bash
git add index.html
git commit -m "Adiciona dashboard web"
git push
```

3. No GitHub, acesse:

```text
Settings → Pages
```

4. Em **Source**, selecione:

```text
Deploy from a branch
```

5. Selecione:

```text
Branch: main
Folder: / (root)
```

6. Salve a configuração.

Após a publicação, o GitHub Pages fornecerá a URL da aplicação.

---

## 🔍 Solução de Problemas — Troubleshooting

### OLED não acende

Verifique:

* alimentação do display;
* conexões SDA e SCL;
* endereço I2C;
* alimentação em 3,3 V ou 5 V conforme o módulo utilizado.

O endereço mais comum do SSD1306 é:

```text
0x3C
```

Caso o display não seja encontrado, utilize um scanner I2C para verificar o endereço real.

> **Atenção:** a tensão de alimentação suportada depende do módulo OLED utilizado. Verifique a especificação da placa antes de aplicar 5 V.

---

### Erro `NameError`

Verifique:

* se todas as bibliotecas necessárias foram enviadas para o ESP32;
* se os nomes das variáveis estão corretos;
* se o arquivo `ssd1306.py` está presente na placa;
* se não existem erros de indentação no `main.py`.

---

### Porta COM ocupada

Se o `esptool` ou o MicroPico não conseguir acessar o ESP32, verifique se o **Serial Monitor** está aberto.

Feche o monitor serial antes de executar comandos como:

```bash
esptool
```

ou realizar o upload do firmware.

---

### DHT11 apresenta timeout

O DHT11 pode apresentar falhas de leitura por problemas de conexão ou temporização.

Verifique:

* alimentação do sensor;
* fio de dados;
* GPIO configurado;
* resistor de pull-up, quando necessário;
* qualidade das conexões.

O código utiliza tratamento de exceções para evitar que uma falha pontual de leitura interrompa completamente a execução do sistema.

---

### Sensor de gás não funciona

Confirme se a flag correspondente está ativada:

```python
USAR_GAS = True
```

Também verifique:

* alimentação do módulo;
* conexão da saída analógica;
* GPIO utilizado;
* faixa de tensão da saída;
* configuração do ADC.

---

### BMP280 não é detectado

Verifique:

* conexão SDA;
* conexão SCL;
* alimentação;
* endereço I2C;
* compartilhamento do barramento com o OLED.

O BMP280 e o OLED podem compartilhar os mesmos pinos I2C, desde que possuam endereços diferentes.

---

## 📁 Estrutura Sugerida do Projeto

```text
estacao-meteorologica/
│
├── firmware/
│   ├── boot.py
│   ├── main.py
│   └── ssd1306.py
│
├── web/
│   └── index.html
│
├── README.md
└── .gitignore
```

---

## 🧠 Tecnologias Utilizadas

| Tecnologia                  | Utilização                             |
| --------------------------- | -------------------------------------- |
| **ESP32**                   | Microcontrolador e conectividade Wi-Fi |
| **MicroPython**             | Desenvolvimento do firmware            |
| **DHT11**                   | Temperatura e umidade                  |
| **LDR**                     | Luminosidade                           |
| **MQ-2 / MQ-135**           | Gás e fumaça                           |
| **BMP280**                  | Pressão atmosférica                    |
| **SSD1306**                 | Display OLED                           |
| **I2C**                     | Comunicação com periféricos            |
| **HTTP / REST**             | Comunicação com a API                  |
| **ThingSpeak**              | Armazenamento dos dados na nuvem       |
| **HTML / CSS / JavaScript** | Desenvolvimento do dashboard           |
| **GitHub Pages**            | Hospedagem da interface web            |

---

## 🎓 Contexto Acadêmico

O projeto foi desenvolvido com finalidade acadêmica, demonstrando a integração entre:

```text
Hardware
   +
Programação Embarcada
   +
Sensores
   +
Internet das Coisas (IoT)
   +
APIs
   +
Computação em Nuvem
   +
Desenvolvimento Web
```

A proposta demonstra, na prática, um fluxo completo de **Internet das Coisas (IoT)**, desde a aquisição dos dados físicos até sua disponibilização em uma interface web.

---

## 📌 Status do Projeto

**Status:** Em desenvolvimento / projeto acadêmico

### Funcionalidades implementadas

* [x] Leitura de temperatura
* [x] Leitura de umidade
* [x] Leitura de luminosidade
* [x] Suporte a sensor de gás
* [x] Suporte a sensor de pressão
* [x] Display OLED
* [x] Conexão Wi-Fi
* [x] Envio de dados para ThingSpeak
* [x] Dashboard Web
* [x] Hospedagem via GitHub Pages
* [x] Alternância de tema baseada na luminosidade

---

## 👨‍💻 Autor

**Projeto Acadêmico — Estação Meteorológica Inteligente IoT**

Desenvolvido utilizando ESP32, MicroPython, sensores ambientais, ThingSpeak e tecnologias web.
