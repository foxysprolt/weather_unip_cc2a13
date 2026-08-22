// CONFIGURAÇÕES DE INTEGRAÇÃO
const GITHUB_REPO = "foxysprolt/weather_unip_cc2a13"; // <--- ALTERE AQUI (ex: "rafael/esp32-weather")
const CHANNEL_ID = '3465259';
const WRITE_API_KEY = 'OGC5WGBQU4OU3GJA';
const READ_API_KEY = 'E6VGVV45AMAC0205';

let urlFirmwareMaisRecente = "";
let versaoMaisRecente = "";
let versaoAtualESP = "";

// 1. AUTENTICAÇÃO
function autenticar() {
  const u = document.getElementById('login-user').value;
  const p = document.getElementById('login-pass').value;

  if (u === "admin" && p === "admin") {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    
    carregarDadosSensores();
    setInterval(carregarDadosSensores, 15000);
  } else {
    document.getElementById('login-error').innerText = "Usuário ou senha incorretos!";
  }
}

function logout() {
  document.getElementById('dashboard').style.display = 'none';
  document.getElementById('login-screen').style.display = 'block';
}

// 2. CONSULTA API DO GITHUB
async function checarUltimaVersaoGitHub() {
  const githubUrl = `https://api.github.com/repos/${GITHUB_REPO}/releases/latest`;
  const statusEl = document.getElementById('firmware-status');
  const btnEl = document.getElementById('btn-ota');

  try {
    const res = await fetch(githubUrl);
    if (!res.ok) throw new Error("Release não encontrada");

    const data = await res.json();
    versaoMaisRecente = data.tag_name;

    const assetBin = data.assets.find(a => a.name.endsWith('.bin'));

    if (assetBin) {
      urlFirmwareMaisRecente = assetBin.browser_download_url;
      
      // Compara Versão do ESP32 (field3) com a Release do GitHub
      if (versaoAtualESP && versaoAtualESP.trim() === versaoMaisRecente.trim()) {
        statusEl.innerText = "O dispositivo já está na versão mais recente!";
        statusEl.style.color = "#94a3b8";
        btnEl.disabled = true;
        btnEl.innerText = "SISTEMA ATUALIZADO";
      } else {
        statusEl.innerText = `Nova Versão Disponível: ${versaoMaisRecente}`;
        statusEl.style.color = "#10b981";
        btnEl.disabled = false;
        btnEl.innerText = `🚀 INSTALAR VERSÃO ${versaoMaisRecente}`;
      }
    } else {
      statusEl.innerText = "Nenhum arquivo .bin anexado na Release.";
    }
  } catch (err) {
    statusEl.innerText = "Sem atualizações ou repositório privado.";
  }
}

// 3. COMANDAR O OTA VIA THINGSPEAK
async function dispararAtualizacao() {
  if (!urlFirmwareMaisRecente) {
    alert("Nenhuma atualização pronta no GitHub!");
    return;
  }

  const statusEl = document.getElementById('firmware-status');
  statusEl.innerText = "Enviando ordem de atualização ao ESP32...";

  const updateUrl = `https://api.thingspeak.com/update?api_key=${WRITE_API_KEY}&field4=1`;

  try {
    const res = await fetch(updateUrl);
    if (res.ok) {
      statusEl.innerText = `Comando enviado! ESP32 baixando versão ${versaoMaisRecente}...`;
      document.getElementById('btn-ota').disabled = true;
    }
  } catch (err) {
    alert("Erro ao enviar comando de atualização.");
  }
}

// 4. LEITURA DOS SENSORES E VERSÃO DO ESP32 (THINGSPEAK)
async function carregarDadosSensores() {
  const readUrl = `https://api.thingspeak.com/channels/${CHANNEL_ID}/feeds.json?results=1&api_key=${READ_API_KEY}`;
  try {
    const res = await fetch(readUrl);
    const data = await res.json();
    const feed = data.feeds[0];

    document.getElementById('dash-temp').innerText = parseFloat(feed.field1).toFixed(1);
    document.getElementById('dash-umid').innerText = Math.round(feed.field2);
    
    // Lê a versão atual enviada pelo ESP32 no field3
    versaoAtualESP = feed.field5 ? feed.field5 : "v1.0.0"; // Lê do field5!
    document.getElementById('esp-version').innerText = versaoAtualESP;

    const d = new Date(feed.created_at);
    document.getElementById('dash-data').innerText = d.toLocaleTimeString('pt-BR');

    // Valida com o Git após obter a versão atual
    checarUltimaVersaoGitHub();
  } catch (e) {
    console.error("Erro ao carregar sensores:", e);
  }
}