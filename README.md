# Documentação Técnica — Weather Intelligence (ESP32 + Dashboard Web)

## 1. Visão geral da arquitetura

O projeto tem 3 partes que conversam entre si, mas nunca diretamente — tudo passa pelo **ThingSpeak** (uma plataforma gratuita de IoT que funciona como "banco de dados na nuvem" com uma API simples de HTTP):

```
[ESP32 + sensores]  --HTTP-->  [ThingSpeak]  <--HTTP--  [Dashboard Web (navegador)]
       |                                                        |
       |<------------------- comando de OTA via flag ---------->|
```

- O **ESP32** lê os sensores a cada 15s e envia os valores pro ThingSpeak (`enviarDadosECheck()`).
- O **site (index.html + app.js)** lê esses mesmos valores do ThingSpeak a cada 15s e atualiza a tela — o navegador nunca fala direto com o ESP32.
- O **cockpit (cockpit.html + cockpit.js)** é um painel admin que checa se existe uma release nova no GitHub e, se o usuário confirmar, "liga uma flag" no ThingSpeak (`field4 = 1`).
- O **ESP32** fica perguntando pro ThingSpeak "essa flag está ligada?" (`checarComandoOTA()`) e, se estiver, baixa o `.bin` direto do GitHub e se autoatualiza (OTA = *Over-The-Air update*, atualização de firmware sem cabo USB).

Essa é a ideia central pra explicar no trabalho: **o ThingSpeak funciona como intermediário/mensageiro entre o hardware e o site**, porque o ESP32 não tem IP público fixo e não dá pra o navegador acessá-lo diretamente pela internet.

---

## 2. Firmware do ESP32 (`main.cpp` — C++ com framework Arduino)

### 2.1 Includes (bibliotecas)

```cpp
#include <WiFi.h>          // conecta o ESP32 numa rede Wi-Fi
#include <HTTPClient.h>    // faz requisições HTTP (GET/POST) para APIs
#include <HTTPUpdate.h>    // baixa um .bin da internet e regrava a memória flash (OTA)
#include <DHT.h>           // lê o sensor de temperatura/umidade DHT11
#include <Wire.h>          // protocolo I2C, usado pra o display se comunicar
#include <Adafruit_GFX.h>  // biblioteca gráfica genérica (desenha formas/texto)
#include <Adafruit_SSD1306.h> // driver específico do display OLED usado
```

### 2.2 Constantes e variáveis globais

```cpp
const String FIRMWARE_VERSION = "v1.3.8";
const String GITHUB_BIN_URL = "https://github.com/.../firmware.bin";
```
Guardam a versão atual do firmware (que é enviada pro ThingSpeak em `field5`, pra o site saber comparar com a versão do GitHub) e o link fixo do arquivo binário que será baixado no OTA.

```cpp
const char* WIFI_SSID = "Ester 2.4G";
const char* WIFI_PASS = "Ester3600";
const char* CHANNEL_ID = "3465259";
const char* WRITE_API_KEY = "OGC5WGBQU4OU3GJA";
const char* READ_API_KEY = "E6VGVV45AMAC0205";
```
Credenciais de Wi-Fi e as chaves do ThingSpeak. `WRITE_API_KEY` é usada pra **enviar** dados (função `enviarDadosECheck`), e `READ_API_KEY` pra **ler** dados (função `checarComandoOTA`) — o ThingSpeak separa as duas permissões por segurança.

> **Observação pro trabalho:** essas chaves estão "hardcoded" (escritas direto no código). Em um projeto real isso é considerado má prática de segurança, porque qualquer pessoa que baixar o firmware ou o código-fonte teria acesso às chaves. O ideal seria usar um arquivo separado ignorado pelo Git (`.gitignore`) ou variáveis de ambiente.

```cpp
#define DHTPIN 4
#define DHTTYPE DHT11
#define LDR_PIN 15
#define GAS_PIN 2
```
`#define` cria uma constante que é substituída no código antes de compilar (não ocupa memória em tempo de execução). Aqui definem em qual pino físico do ESP32 cada sensor está ligado.

```cpp
DHT dht(DHTPIN, DHTTYPE);
```
Cria um **objeto** da classe `DHT` (programação orientada a objetos) — é assim que a biblioteca sabe qual pino ler e qual modelo de sensor interpretar.

```cpp
unsigned long lastTime = 0;
const unsigned long timerDelay = 15000;
```
`unsigned long` guarda números inteiros grandes sem sinal (não-negativos) — usado aqui pra guardar tempo em milissegundos (`millis()` do Arduino nunca é negativo e cresce demais pra caber num `int` normal por muito tempo). `timerDelay = 15000` é o intervalo de 15 segundos entre cada envio de dados.

### 2.3 `desenharHeader()` — desenha o cabeçalho do display

```cpp
void desenharHeader(const char* titulo) {
  display.clearDisplay();
  display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
  display.fillRect(0, 0, 128, 14, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK);
  ...
  display.println(titulo);
  display.setTextColor(SSD1306_WHITE);
}
```
Função auxiliar (chamada por várias outras) que desenha uma moldura, uma barra branca no topo com o texto em preto (invertido) e depois volta a cor pro branco padrão. Recebe `const char*` (um texto/string em C, mais leve que `String`) como parâmetro pra reaproveitar o mesmo desenho com títulos diferentes — isso evita repetir esse bloco de código em cada tela.

### 2.4 `atualizarOLED()` — alterna as 4 telas do display

```cpp
if (millis() - ultimaTrocaTela > 3000) {
  telaAtual = (telaAtual + 1) % 4;
  ultimaTrocaTela = millis();
}
```
Esse é o padrão **"delay sem bloquear"** (non-blocking delay), muito comum em Arduino: em vez de usar `delay(3000)` (que travaria todo o programa por 3s, incluindo a leitura de sensores), ele compara o tempo atual (`millis()`) com o tempo da última troca. Se passaram mais de 3000ms, troca de tela. O operador `%` (módulo/resto da divisão) faz o contador voltar pra 0 depois de chegar em 3, criando um ciclo 0→1→2→3→0...

O `switch (telaAtual)` decide qual das 4 telas desenhar (temperatura, umidade, luminosidade, gás), cada uma chamando `desenharHeader()` e depois escrevendo o valor correspondente.

### 2.5 `executarOTA()` — baixa e instala o firmware novo

```cpp
WiFiClientSecure client;
client.setInsecure();
```
Cria uma conexão HTTPS (criptografada). `setInsecure()` desativa a verificação do certificado SSL do servidor — é um atalho comum em projetos de estudante/hobby porque validar certificados no ESP32 dá trabalho (precisa embutir o certificado raiz), mas **não é recomendado em produção** porque abre brecha pra ataques "man-in-the-middle".

```cpp
httpUpdate.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
```
O link do GitHub Releases redireciona (HTTP 302) pra um link real da Amazon AWS onde o arquivo fica hospedado. Essa linha diz pro ESP32 seguir esse redirecionamento automaticamente, senão o download falha.

```cpp
httpUpdate.rebootOnUpdate(false);
t_httpUpdate_return ret = httpUpdate.update(client, GITHUB_BIN_URL);
```
`httpUpdate.update()` é a função que faz todo o trabalho pesado: baixa o `.bin` e regrava a memória flash do ESP32 na partição de aplicação livre (por isso o projeto precisa de duas partições de app — pra sempre ter uma pra gravar enquanto a outra roda). `rebootOnUpdate(false)` evita que ela reinicie sozinha, permitindo mostrar uma mensagem na tela antes.

```cpp
switch (ret) {
  case HTTP_UPDATE_FAILED: ...
  case HTTP_UPDATE_NO_UPDATES: ...
  case HTTP_UPDATE_OK:
    ...
    ESP.restart();
    break;
}
```
`t_httpUpdate_return` é um **enum** (tipo com valores nomeados fixos) que a biblioteca retorna pra dizer o que aconteceu. Só em caso de sucesso (`HTTP_UPDATE_OK`) o código reinicia o ESP32 com `ESP.restart()` pra ele já iniciar rodando o firmware novo.

### 2.6 `checarComandoOTA()` — pergunta ao ThingSpeak se deve atualizar

```cpp
String url = "https://api.thingspeak.com/channels/" + String(CHANNEL_ID) + "/fields/4/last.json?api_key=" + String(READ_API_KEY);
http.begin(url);
int httpCode = http.GET();
```
Monta a URL de uma requisição GET que pede o **último valor do campo 4** (`field4`) do canal, em formato JSON. `field4` é usado aqui como uma espécie de "interruptor remoto": o site liga ele (`=1`) quando o admin manda atualizar.

```cpp
if (payload.indexOf("\"field4\":\"1\"") != -1) {
```
`indexOf()` procura esse trecho de texto dentro da resposta JSON. Se encontrar (`!= -1` significa "encontrou em alguma posição"), significa que a flag está ligada.

```cpp
http.end();
HTTPClient resetHttp;
String resetUrl = "https://api.thingspeak.com/update?api_key=" + String(WRITE_API_KEY) + "&field4=0";
resetHttp.begin(resetUrl);
resetHttp.GET();
resetHttp.end();
```
Antes de atualizar, o código **reseta a flag de volta pra 0** (fazendo outra requisição, agora com a `WRITE_API_KEY`) — assim, depois que o ESP32 reiniciar com o firmware novo, ele não vai entender que precisa atualizar de novo em loop infinito.

### 2.7 `enviarDadosECheck()` — lê sensores e envia pro ThingSpeak

```cpp
float h = dht.readHumidity();
float t = dht.readTemperature();
if (isnan(h) || isnan(t)) { ... return; }
```
Lê os dois valores do sensor DHT11. `isnan()` ("is not a number") verifica se a leitura falhou — sensores desse tipo às vezes retornam um valor inválido por ruído elétrico ou timing errado na comunicação, então essa checagem evita mandar lixo pro banco de dados.

```cpp
int leituraDigital = digitalRead(LDR_PIN);
luzG = (leituraDigital == LOW) ? 4095 : 0;
```
O LDR (sensor de luminosidade) aqui está ligado num pino **digital**, não analógico — então só retorna `HIGH` ou `LOW`. O operador ternário (`condição ? valorSeVerdadeiro : valorSeFalso`) converte isso pra uma escala de 0 a 4095 (a mesma escala que um pino analógico do ESP32 usaria), só pra manter compatibilidade com o que o dashboard espera receber.

```cpp
gasG = analogRead(GAS_PIN);
```
Já o sensor de gás está num pino **analógico** de verdade, então `analogRead()` retorna um valor proporcional à tensão captada (0 a 4095 no ESP32, que tem ADC de 12 bits).

```cpp
String url = "https://api.thingspeak.com/update?api_key=" + String(WRITE_API_KEY);
url += "&field1=" + String(t);
url += "&field2=" + String(h);
url += "&field3=" + String(luzG);
url += "&field5=" + FIRMWARE_VERSION;
url += "&field6=" + String(gasG);
```
Monta a URL de atualização concatenando cada sensor num campo diferente do ThingSpeak (`field1`=temperatura, `field2`=umidade, `field3`=luz, `field5`=versão do firmware, `field6`=gás — repare que `field4` fica de fora de propósito, porque é reservado pro comando de OTA).

No final, `checarComandoOTA()` é chamada — ou seja, toda vez que o ESP32 termina de enviar seus dados, ele já aproveita e checa se tem atualização pendente, em vez de ter dois temporizadores separados.

### 2.8 `setup()` — roda uma única vez, ao ligar/reiniciar

Inicializa o `Serial` (monitor de depuração via USB), configura os pinos como entrada (`INPUT`), reinicia o barramento I2C (`Wire.end()` + `Wire.begin(21, 22)` — pinos 21/22 são o padrão SDA/SCL do ESP32), inicializa o display, o sensor DHT, e por fim conecta no Wi-Fi com um `while` que fica esperando (`WiFi.status() != WL_CONNECTED`) até a conexão ser estabelecida.

### 2.9 `loop()` — roda infinitamente

```cpp
void loop() {
  atualizarOLED();
  if ((millis() - lastTime) > timerDelay) {
    if (WiFi.status() == WL_CONNECTED) {
      enviarDadosECheck();
    }
    lastTime = millis();
  }
}
```
`atualizarOLED()` roda em **toda** iteração do loop (bem rápido, milhares de vezes por segundo), garantindo que a troca de tela pareça suave. Já `enviarDadosECheck()` só roda quando passam 15 segundos — de novo, o padrão "delay sem bloquear" pra não travar o display enquanto espera a resposta da rede.

---

## 3. `platformio.ini` — arquivo de configuração do projeto

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
```
Define o **ambiente de compilação**: qual fabricante de chip (`espressif32`), qual placa exata (`esp32dev`, uma placa genérica de desenvolvimento) e qual framework de programação usar (`arduino`, que dá acesso a funções como `digitalRead`, `Serial`, etc. — a alternativa seria o ESP-IDF puro, mais baixo nível).

```ini
lib_deps =
    mathworks/ThingSpeak @ ^2.0.0
    adafruit/DHT sensor library @ ^1.4.6
    ...
```
Lista de **dependências externas** (bibliotecas de terceiros) que o PlatformIO baixa automaticamente do registro dele. O `^2.0.0` é *semantic versioning*: aceita qualquer versão compatível a partir da 2.0.0 (ex: 2.1.5) mas nunca pula pra uma versão major diferente (ex: 3.0.0), que poderia ter mudanças que quebram o código.

```ini
board_build.partitions = min_spiffs.csv
```
Escolhe como a memória flash de 4MB é dividida internamente. Esse esquema específico reserva bem pouco espaço pro sistema de arquivos (SPIFFS, não usado nesse projeto) e mais espaço pras **duas partições de aplicação** necessárias pro OTA funcionar (uma partição roda enquanto a outra recebe o firmware novo).

```ini
build_flags =
    -Os
    -DCORE_DEBUG_LEVEL=0
```
Instruções extras pro compilador: `-Os` pede pra otimizar o código gerado priorizando **tamanho** em vez de velocidade (existe também `-O2`/`-O3` que otimizam pra velocidade, gerando binários maiores). `-DCORE_DEBUG_LEVEL=0` desativa os logs internos de depuração do framework Espressif, que também economiza espaço.

---

## 4. JavaScript do site (`app.js`, `cockpit.js`, `historico.js`)

### 4.1 Conceitos de JS usados em todos os arquivos

- **`async function` / `await`**: forma moderna de lidar com operações que demoram (como uma requisição de rede) sem travar a página. `await` "pausa" a função até a resposta chegar, mas sem travar o navegador inteiro.
- **`fetch()`**: função nativa do navegador pra fazer requisições HTTP, parecida com o `HTTPClient` do C++.
- **Template literals** (crase `` ` `` em vez de aspas): permitem inserir variáveis dentro do texto com `${variavel}`, ex: `` `field1=${valor}` ``.
- **`document.getElementById('id')`**: busca um elemento HTML pelo `id` pra poder ler ou mudar seu conteúdo via JS — é a ponte entre o HTML estático e os dados dinâmicos.

### 4.2 `app.js` (usado no `index.html`, o painel público)

```js
async function carregarDadosSensores() {
  const readUrl = `https://api.thingspeak.com/channels/${CHANNEL_ID}/feeds.json?results=1&api_key=${READ_API_KEY}`;
  const res = await fetch(readUrl);
  const data = await res.json();
  const feed = data.feeds[0];
```
Busca o **último registro** salvo no ThingSpeak (`results=1`) e já converte a resposta de JSON pra objeto JavaScript com `res.json()`.

```js
document.getElementById('dash-temp').innerText = parseFloat(feed.field1).toFixed(1);
```
`parseFloat()` converte o texto vindo da API (que chega sempre como string) pra número decimal. `.toFixed(1)` formata pra sempre mostrar 1 casa decimal. `innerText =` substitui o texto visível daquele elemento HTML — é assim que o número "muda na tela" sem precisar recarregar a página.

```js
versaoAtualESP = feed.field5 ? feed.field5 : "v1.0.0";
```
Operador ternário de novo: se `feed.field5` existir (não for `null`/`undefined`/vazio), usa ele; senão usa `"v1.0.0"` como valor padrão de segurança.

```js
async function checarUltimaVersaoGitHub() {
  const githubUrl = `https://api.github.com/repos/${GITHUB_REPO}/releases/latest`;
  const res = await fetch(githubUrl);
  const data = await res.json();
  versaoMaisRecente = data.tag_name;
  const assetBin = data.assets.find(a => a.name.endsWith('.bin'));
```
Usa a **API pública do GitHub** pra descobrir qual é a última release do repositório. `data.assets.find(...)` percorre a lista de arquivos anexados àquela release e procura o primeiro cujo nome termine em `.bin` (o `=>` é uma *arrow function*, forma resumida de escrever uma função pequena). Depois compara essa versão com a que o ESP32 reportou (`versaoAtualESP`) pra decidir se mostra o botão de atualizar habilitado ou não.

```js
async function dispararAtualizacao() {
  const updateUrl = `https://api.thingspeak.com/update?api_key=${WRITE_API_KEY}&field4=1`;
  const res = await fetch(updateUrl);
  ...
  setTimeout(async () => {
    const resetUrl = `.../update?api_key=${WRITE_API_KEY}&field4=0`;
    await fetch(resetUrl);
  }, 16000);
}
```
Essa é a ação que o **admin** dispara: liga a flag `field4=1` no ThingSpeak (o mesmo sinal que o `checarComandoOTA()` do C++ está esperando encontrar). `setTimeout(fn, 16000)` agenda a execução de `fn` pra daqui 16 segundos — usado aqui como uma segurança extra pra resetar a flag no lado do site também, caso o ESP32 demore a fazer isso sozinho, respeitando o limite do ThingSpeak de 1 requisição a cada 15s por chave.

### 4.3 `cockpit.js` (painel admin)

```js
function autenticar() {
  const u = document.getElementById('login-user').value;
  const p = document.getElementById('login-pass').value;
  if (u === "admin" && p === "admin") {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    carregarDadosSensores();
    setInterval(carregarDadosSensores, 15000);
```
`.value` pega o texto digitado num `<input>`. A "autenticação" aqui é só uma comparação de texto fixo no próprio JavaScript (`"admin"`/`"admin"`) — funciona pra demonstração, mas **não é segurança de verdade**, porque qualquer pessoa pode abrir o código-fonte da página (F12 no navegador) e ler a senha, ou simplesmente forçar `display.style.display='block'` no console. Vale a pena comentar essa limitação no trabalho, como algo a evoluir (autenticação real precisaria de um servidor por trás).

`.style.display = 'none' / 'block'` é como o JS **esconde e mostra** elementos HTML sem precisar trocar de página — a tela de dashboard já existe no HTML o tempo todo, só fica com `display:none` até o login.

`setInterval(funcao, 15000)` roda aquela função repetidamente a cada 15000ms — o "coração" que mantém o painel sempre atualizado sozinho.

O restante do `cockpit.js` reutiliza a mesma lógica de `checarUltimaVersaoGitHub()` e `dispararAtualizacao()` do `app.js`.

### 4.4 `historico.js` (tela de replay, dados simulados)

```js
const dadosHistoricosFakes = [
  { hora: "00:00", temp: 18.2, umid: 85, gas: 320, pressao: 1015 },
  ...
];
```
Um **array de objetos** — cada item representa uma "foto" dos sensores num horário do dia. Como o projeto não guarda histórico real (o ThingSpeak grátis limita o volume de dados salvos), essa tela usa dados inventados só pra demonstrar visualmente como um "replay" funcionaria.

```js
function atualizarPorTimeline(index) {
  const totalItens = dadosHistoricosFakes.length - 1;
  const itemIndex = Math.round((index / 23) * totalItens);
  const dado = dadosHistoricosFakes[itemIndex];
```
O slider HTML (`<input type="range" min="0" max="23">`) representa as 24 horas do dia, mas o array só tem 12 posições (de 2 em 2 horas). Essa conta faz a **conversão de escala**: pega a posição do slider (0-23) e traduz pra um índice válido dentro do array (0-11), arredondando com `Math.round()`.

```js
function alternarPlay() {
  if (!tocando) {
    intervaloPlay = setInterval(() => {
      let val = parseInt(timeline.value) + 1;
      if (val > 23) val = 0;
      timeline.value = val;
      atualizarPorTimeline(val);
    }, 800);
  } else {
    clearInterval(intervaloPlay);
  }
}
```
Implementa o botão Play/Pause: a cada 800ms avança o slider em 1 e chama `atualizarPorTimeline()` de novo, criando o efeito de "passar o tempo sozinho". `clearInterval()` cancela esse temporizador quando o usuário aperta Pause — sem isso, o intervalo continuaria rodando pra sempre em segundo plano.

---

## 5. HTML e CSS (resumo rápido, já que você domina essa parte)

- **`index.html`**: painel público — mostra o widget de clima com abas (umidade/gás/pressão) e um botão que leva pro `cockpit.html`.
- **`cockpit.html`**: tela de login + dashboard admin com o card de gerenciamento de firmware.
- **`historico.html`**: mesmo visual do `index.html`, mas com o player de linha do tempo embaixo.
- **`styles.css` / `cockpit.css`**: usam `backdrop-filter: blur()` pra criar o efeito "vidro fosco" (glassmorphism), `@keyframes` pra animar a onda da umidade e a troca de tela, e a classe `.light-mode` que é adicionada/removida via JS (não CSS puro) pra alternar entre tema claro e escuro conforme a luminosidade lida pelo LDR.

---

## 6. Glossário rápido pra documentação

| Termo | Significado |
|---|---|
| **OTA** | *Over-The-Air* — atualizar o firmware pela rede, sem plugar cabo USB |
| **API** | *Application Programming Interface* — forma padronizada de dois sistemas trocarem dados (aqui, sempre via HTTP) |
| **JSON** | formato de texto pra representar dados estruturados (`{"chave": "valor"}`), usado nas respostas das APIs |
| **ADC** | *Analog-to-Digital Converter* — circuito que converte uma tensão elétrica (analógica) num número (digital) |
| **I2C** | protocolo de comunicação entre chips usando só 2 fios (SDA/SCL) — usado aqui pro display OLED |
| **Flash** | memória permanente onde o firmware fica gravado (equivale ao "HD" do ESP32) |
| **Heap** | memória RAM usada para alocações dinâmicas (como `String`) durante a execução |
| **Semantic Versioning** | padrão `MAJOR.MINOR.PATCH` (ex: `2.1.5`) pra numerar versões de software |