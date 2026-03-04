const regimeEl = document.getElementById("regime");
const regimeBlurbEl = document.getElementById("regime-blurb");
const confidenceEl = document.getElementById("confidence");
const timestampEl = document.getElementById("timestamp");
const modelStatusEl = document.getElementById("model-status");
const dataStatusEl = document.getElementById("data-status");
const featureCountEl = document.getElementById("feature-count");
const classesEl = document.getElementById("classes");
const thresholdsEl = document.getElementById("thresholds");
const briefingEl = document.getElementById("briefing");
const probabilityListEl = document.getElementById("probability-list");
const ringFillEl = document.getElementById("ring-fill");

const regimeCopy = {
  RiskOn: {
    blurb: "Risk appetite is leading. Trend and momentum conditions are supportive.",
    briefing:
      "This regime suggests a constructive tape. Equities typically behave better when volatility stays contained and directional strength persists across the market complex.",
    color: "#7dffa1",
  },
  RiskOff: {
    blurb: "Defensive positioning is dominating. Capital preservation is the priority.",
    briefing:
      "This regime signals a more cautious environment. Markets in this state often reward defensive assets while cyclical exposure and leverage become less forgiving.",
    color: "#ff6b7a",
  },
  HighVol: {
    blurb: "Instability is elevated. Fast repricing and larger swings are in control.",
    briefing:
      "This is the unstable state. Volatility-driven moves can overwhelm slower signals, so traders generally expect wider ranges, faster rotations, and more fragile sentiment.",
    color: "#ffb347",
  },
};

function formatTimestamp(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "TIMESTAMP UNAVAILABLE"
    : `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

function updateRing(confidence, color) {
  const circumference = 301.59;
  ringFillEl.style.strokeDashoffset = `${circumference * (1 - confidence)}`;
  ringFillEl.style.stroke = color;
}

function renderProbabilities(probabilities) {
  probabilityListEl.innerHTML = "";
  Object.entries(probabilities)
    .sort((a, b) => b[1] - a[1])
    .forEach(([label, value]) => {
      const wrapper = document.createElement("div");
      wrapper.className = "probability-item";
      wrapper.innerHTML = `
        <div class="probability-head">
          <span>${label}</span>
          <strong>${(value * 100).toFixed(1)}%</strong>
        </div>
        <div class="probability-bar"><div style="width:${(value * 100).toFixed(1)}%"></div></div>
      `;
      probabilityListEl.appendChild(wrapper);
    });
}

async function loadMetadata() {
  const [healthResponse, metadataResponse] = await Promise.all([
    fetch("/health"),
    fetch("/metadata"),
  ]);

  const health = await healthResponse.json();
  const metadata = await metadataResponse.json();

  modelStatusEl.textContent = health.model_loaded ? "ONLINE" : "OFFLINE";
  dataStatusEl.textContent = health.data_available ? "READY" : "MISSING";
  featureCountEl.textContent = metadata.features.length;
  classesEl.textContent = metadata.classes.join(" / ");
  thresholdsEl.textContent = Object.entries(metadata.thresholds)
    .map(([key, value]) => `${key}:${value}`)
    .join("  ");
}

async function loadPrediction() {
  const response = await fetch("/predict/latest", { method: "POST" });
  if (!response.ok) {
    throw new Error("Prediction request failed.");
  }

  const data = await response.json();
  const copy = regimeCopy[data.regime] || {
    blurb: "Current regime available.",
    briefing: "Model output received.",
    color: "#4de2ff",
  };

  regimeEl.textContent = data.regime.toUpperCase();
  regimeEl.style.color = copy.color;
  regimeBlurbEl.textContent = copy.blurb;
  confidenceEl.textContent = `${Math.round(data.confidence * 100)}%`;
  timestampEl.textContent = formatTimestamp(data.timestamp);
  briefingEl.innerHTML = `<p>${copy.briefing}</p><p>Source: ${data.source}</p>`;
  updateRing(data.confidence, copy.color);
  renderProbabilities(data.probabilities);
}

async function boot() {
  try {
    await loadMetadata();
    await loadPrediction();
  } catch (error) {
    regimeEl.textContent = "ERROR";
    regimeEl.style.color = "#ff6b7a";
    regimeBlurbEl.textContent = "Unable to fetch model output. Check API startup and artifacts.";
    briefingEl.innerHTML = "<p>The dashboard could not load live inference data.</p>";
    modelStatusEl.textContent = "ERROR";
    dataStatusEl.textContent = "CHECK";
    timestampEl.textContent = "SYNC FAILED";
  }
}

boot();
setInterval(loadPrediction, 30000);
