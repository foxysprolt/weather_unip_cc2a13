// DADOS SIMULADOS (FAKES) PARA TESTAR O PLAYER DE TEMPO
const dadosHistoricosFakes = [
    { hora: "00:00", temp: 18.2, umid: 85, gas: 320, pressao: 1015 },
    { hora: "02:00", temp: 17.5, umid: 88, gas: 310, pressao: 1016 },
    { hora: "04:00", temp: 16.8, umid: 92, gas: 300, pressao: 1017 },
    { hora: "06:00", temp: 18.0, umid: 80, gas: 350, pressao: 1015 },
    { hora: "08:00", temp: 22.4, umid: 70, gas: 410, pressao: 1014 },
    { hora: "10:00", temp: 26.1, umid: 58, gas: 480, pressao: 1012 },
    { hora: "12:00", temp: 31.5, umid: 42, gas: 520, pressao: 1009 },
    { hora: "14:00", temp: 33.2, umid: 38, gas: 550, pressao: 1008 },
    { hora: "16:00", temp: 29.8, umid: 48, gas: 600, pressao: 1010 },
    { hora: "18:00", temp: 24.5, umid: 62, gas: 450, pressao: 1012 },
    { hora: "20:00", temp: 21.0, umid: 75, gas: 380, pressao: 1014 },
    { hora: "22:00", temp: 19.3, umid: 81, gas: 340, pressao: 1015 }
];

let tocando = false;
let intervaloPlay = null;

// TROCA DE ABAS
function trocarAba(nomeAba, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    btn.classList.add('active');
    document.getElementById(`pane-${nomeAba}`).classList.add('active');
}

// FRASES NO PASSADO PARA O REPLAY TEMPORAL
function obterFraseHistorico(temp) {
    if (temp >= 33) return "Estava um forno! O povo devia estar lotando a praia nesse horário 🏖️🔥";
    if (temp >= 30) return "Fazendo um calorão! Hora perfeita em que o pessoal estava na piscina 🏊‍♂️🍹";
    if (temp >= 27) return "Calorzinho bom registrado! Bateu até aquela vontade de um sorvete 🍦🥤";
    if (temp >= 24) return "Temperatura perfeita na época! Clima ideal que fez para passear 🌤️🍃";
    if (temp >= 21) return "Estava um clima ameno e suave! Nem quente, nem frio nesse horário 🌿✨";
    if (temp >= 18) return "Bateu um ventinho fresco! Quem estava na rua precisou de um casaco 🧥💨";
    if (temp >= 15) return "A temperatura caiu! Momento perfeito em que um café veio a calhar ☕🥐";
    if (temp >= 12) return "Fazia um friozinho gostoso! Todo mundo preferiu se enrolar no edredom 🛋️❄️";
    return "Congelante! Um dos horários mais frios registrados no período 🥶🧊";
}

// ATUALIZA OS VALORES CONFORME A BARRA DO PLAYER É ARRASTADA
function atualizarPorTimeline(index) {
    const totalItens = dadosHistoricosFakes.length - 1;
    const itemIndex = Math.round((index / 23) * totalItens);
    const dado = dadosHistoricosFakes[itemIndex];

    document.getElementById('hora-selecionada').innerText = dado.hora;

    // 1. TEMPERATURA E FRASE NO PASSADO
    document.getElementById('dash-temp').innerText = dado.temp.toFixed(1);
    const tempMsgElem = document.getElementById('dash-temp-msg');
    if (tempMsgElem) {
        tempMsgElem.innerText = obterFraseHistorico(dado.temp);
    }

    // 2. UMIDADE (ÁGUA SUBINDO E DESCENDO)
    document.getElementById('dash-umid').innerText = dado.umid;
    document.getElementById('nivel-agua').style.height = `${dado.umid}%`;

    // 3. GÁS
    document.getElementById('dash-gas').innerText = dado.gas;

    // 4. PRESSÃO (BEXIGA CRESCENDO)
    document.getElementById('dash-pressao').innerText = dado.pressao;
    const escala = (dado.pressao - 900) / 150;
    const fator = Math.max(0.6, Math.min(escala, 2.0));
    document.getElementById('dash-bexiga').style.transform = `scale(${fator})`;
}

// BOTÃO PLAY / PAUSE
function alternarPlay() {
    const btn = document.getElementById('btn-play');
    const timeline = document.getElementById('timeline');

    if (!tocando) {
        tocando = true;
        btn.innerText = "⏸ Pause";
        intervaloPlay = setInterval(() => {
            let val = parseInt(timeline.value) + 1;
            if (val > 23) val = 0;
            timeline.value = val;
            atualizarPorTimeline(val);
        }, 800);
    } else {
        tocando = false;
        btn.innerText = "▶ Play";
        clearInterval(intervaloPlay);
    }
}

// Inicializa o player no meio do dia
atualizarPorTimeline(12);