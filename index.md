<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="author" content="foxysprolt">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Weather Intelligence - Dashboard</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    body {
      background-color: var(--bg);
      color: var(--text-main);
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
    }

    .container {
      background-color: var(--card-bg);
      width: 100%;
      max-width: 400px;
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Tela Inicial: Principal */
    .main-display {
      text-align: center;
      padding-bottom: 24px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .date {
      color: var(--text-sub);
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .temp-large {
      font-size: 4rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 10px 0;
    }

    .status {
      font-size: 1rem;
      color: var(--accent);
      font-weight: 500;
    }

    /* Área dos Botões Clicáveis */
    .sensor-menu {
      margin-top: 20px;
      display: flex;
      gap: 10px;
      justify-content: space-between;
    }

    .btn-sensor {
      flex: 1;
      background-color: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--text-main);
      padding: 12px 8px;
      border-radius: 12px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
      transition: all 0.2s ease;
    }

    .btn-sensor:hover {
      background-color: rgba(255, 255, 255, 0.1);
    }

    .btn-sensor.active {
      background-color: var(--accent);
      color: #000;
      border-color: var(--accent);
    }

    /* Painel do Sensor Selecionado */
    .sensor-details {
      margin-top: 20px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 16px;
      padding: 16px;
      text-align: center;
      min-height: 90px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .detail-title {
      font-size: 0.8rem;
      color: var(--text-sub);
      text-transform: uppercase;
      margin-bottom: 6px;
    }

    .detail-value {
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--text-main);
    }

    .detail-status {
      font-size: 0.75rem;
      margin-top: 4px;
      color: #4ade80; /* verde para normal */
    }
  </style>
</head>
<body>

  <div class="container">
    <!-- Informações Principais (Temperatura + Dia) -->
    <div class="main-display">
      <div class="date" id="current-date">Quarta-feira, 19 de Ago</div>
      <div class="temp-large"><span id="temp-val">24.5</span>°C</div>
      <div class="status">Céu Limpo</div>
    </div>

    <!-- Botões para Revelar Outros Sensores -->
    <div class="sensor-menu">
      <button class="btn-sensor active" onclick="mostrarSensor('umidade', this)">Umidade</button>
      <button class="btn-sensor" onclick="mostrarSensor('gas', this)">Gás/Fumaça</button>
      <button class="btn-sensor" onclick="mostrarSensor('pressao', this)">Pressão</button>
    </div>

    <!-- Painel de Detalhes Exibido ao Clicar -->
    <div class="sensor-details">
      <div class="detail-title" id="sensor-nome">Umidade Relativa</div>
      <div class="detail-value" id="sensor-valor">62 %</div>
      <div class="detail-status" id="sensor-status">Nível ideal</div>
    </div>
  </div>

  <script>
    // Dados simulados que depois serão preenchidos pela sua API Adafruit IO / ESP32
    const dadosSensores = {
      umidade: {
        nome: "Umidade Relativa (DHT11)",
        valor: "62 %",
        status: "Nível ideal",
        corStatus: "#4ade80"
      },
      gas: {
        nome: "Detector de Gás (MQ-2)",
        valor: "120 PPM",
        status: "Ar Seguro / Sem Vazamento",
        corStatus: "#4ade80"
      },
      pressao: {
        nome: "Pressão Atmosférica (BMP280)",
        valor: "1013 hPa",
        status: "Estável (Nível do Mar)",
        corStatus: "#38bdf8"
      }
    };

    function mostrarSensor(tipo, botao) {
      // Remove a classe 'active' de todos os botões e adiciona no clicado
      document.querySelectorAll('.btn-sensor').forEach(b => b.classList.remove('active'));
      botao.classList.add('active');

      // Atualiza os dados no painel inferior
      const sensor = dadosSensores[tipo];
      document.getElementById('sensor-nome').innerText = sensor.nome;
      document.getElementById('sensor-valor').innerText = sensor.valor;

      const elemStatus = document.getElementById('sensor-status');
      elemStatus.innerText = sensor.status;
      elemStatus.style.color = sensor.corStatus;
    }
  </script>
</body>
</html>