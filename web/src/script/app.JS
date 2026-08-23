const CHANNEL_ID = '3465259';
const READ_API_KEY = 'E6VGVV45AMAC0205';

const url = `https://api.thingspeak.com/channels/${CHANNEL_ID}/feeds.json?results=1&api_key=${READ_API_KEY}`;

async function carregarDadosClima() {
  try {
    const response = await fetch(url);
    if (!response.ok && response.status !== 304) return;

    const data = await response.json();
    const feeds = data.feeds;
    if (!feeds || feeds.length === 0) return;

    const ultimaLeitura = feeds[feeds.length - 1];

    const temp = parseFloat(ultimaLeitura.field1) || 0;
    const umid = parseFloat(ultimaLeitura.field2) || 0;
    const luzRaw = parseInt(ultimaLeitura.field3) || 0;

    // 1. Data e Hora
    const elData = document.getElementById('dash-data');
    if (elData && ultimaLeitura.created_at) {
      const dataObj = new Date(ultimaLeitura.created_at);
      elData.innerText = `ÚLTIMA ATUALIZAÇÃO: ${dataObj.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
    }

    // 2. Temperatura
    const elTemp = document.getElementById('dash-temp');
    if (elTemp) elTemp.innerText = temp.toFixed(1);

    const elMsgTemp = document.getElementById('dash-temp-msg');
    if (elMsgTemp) {
      if (temp >= 30) elMsgTemp.innerText = "Muito Quente! Ambiente abafado.";
      else if (temp >= 20) elMsgTemp.innerText = "Clima Agradável";
      else elMsgTemp.innerText = "Ambiente Frio";
    }

    // 3. Umidade
    const elUmid = document.getElementById('dash-umid');
    if (elUmid) elUmid.innerText = Math.round(umid);

    const elAgua = document.getElementById('nivel-agua');
    if (elAgua) elAgua.style.height = `${Math.min(umid, 100)}%`;

    // 4. TROCA DE MODO DARK/WHITE PELO LDR DIGITAL
    const body = document.body;
    const widget = document.getElementById('main-widget');

    if (luzRaw > 2000) {
      // Luz detectada pelo módulo -> Modo Claro
      body.classList.add('light-mode');
      if (widget) widget.classList.add('light-mode');
    } else {
      // Pouca luz / Escuro -> Modo Escuro (Padrão)
      body.classList.remove('light-mode');
      if (widget) widget.classList.remove('light-mode');
    }
    // Gás
const gasPpm = parseInt(ultimaLeitura.field6) || 0;

const elGas = document.getElementById('dash-gas');
const elGasMsg = document.getElementById('dash-gas-msg');
const cardGas = document.getElementById('card-gas');

if (elGas) elGas.innerText = gasPpm;

if (elGasMsg && cardGas) {
  if (gasPpm > 1500) {
    elGasMsg.innerText = "⚠️ ALERTA: Fumaça/Gás Detectado!";
    cardGas.classList.add('alerta-gas');
  } else {
    elGasMsg.innerText = "Ar puro e ambiente seguro 🌿";
    cardGas.classList.remove('alerta-gas');
  }
}

  } catch (error) {
    console.error("Erro ao carregar dados do ThingSpeak:", error);
  }
}

setInterval(carregarDadosClima, 15000);
carregarDadosClima();

async function abrirPainelOTA() {
  if (confirm("Deseja disparar a atualização remota do ESP32 via GitHub Release?")) {
    const urlGatilho = `https://api.thingspeak.com/update?api_key=OGC5WGBQU4OU3GJA&field4=1`;
    await fetch(urlGatilho);
    alert("Comando de atualização enviado! Em até 15 segundos o ESP32 baixará a nova Release.");
  }
}
