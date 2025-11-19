const grid = document.getElementById("insightsGrid");
const statusBanner = document.getElementById("statusBanner");
const triggerButton = document.getElementById("triggerEtl");

const FALLBACK_INSIGHTS = window.__FALLBACK_INSIGHTS__ ?? [];
const API_BASE =
  window.API_BASE_URL ||
  (window.location.protocol === "file:" || /:(5500|5501)$/i.test(window.location.host)
    ? "http://127.0.0.1:8000"
    : window.location.origin);

let backendAvailable = true;

const setStatus = (message, tone = "idle") => {
  statusBanner.textContent = message;
  statusBanner.dataset.tone = tone;
};

const buildCard = (insight, index) => {
  const card = document.createElement("article");
  card.className = "card";
  card.style.animationDelay = `${index * 120}ms`;
  card.innerHTML = `
    <span>${insight.focus_area}</span>
    <h3>${insight.city}</h3>
    <p>${insight.insight}</p>
  `;
  return card;
};

const renderInsights = (insights) => {
  grid.innerHTML = "";
  if (!insights.length) {
    grid.innerHTML = '<p>Nenhuma iniciativa encontrada ainda.</p>';
    return;
  }
  insights.forEach((insight, index) => {
    grid.appendChild(buildCard(insight, index));
  });
};

const fetchInsights = async () => {
  setStatus("Carregando tendências com dados públicos…", "loading");
  try {
    const response = await fetch(`${API_BASE}/insights`);
    if (!response.ok) throw new Error("Falha ao consultar backend");
    const data = await response.json();
    renderInsights(data);
    backendAvailable = true;
    triggerButton.disabled = false;
    triggerButton.title = "";
    setStatus("Pipeline pronto. Aperte o botão para regenerar com IA.", "idle");
  } catch (error) {
    console.error(error);
    backendAvailable = false;
    triggerButton.disabled = true;
    triggerButton.title = "Inicie o backend FastAPI para liberar esta ação.";
    if (FALLBACK_INSIGHTS.length) {
      renderInsights(FALLBACK_INSIGHTS);
      setStatus("Backend offline. Mostrando insights de fallback.", "error");
    } else {
      setStatus("Não foi possível carregar os dados. Tente novamente.", "error");
    }
  }
};

const triggerEtl = async () => {
  if (!backendAvailable) {
    setStatus("Ative o backend para rodar o ETL com IA.", "error");
    return;
  }
  triggerButton.disabled = true;
  setStatus("Rodando ETL com IA…", "loading");
  try {
    const response = await fetch(`${API_BASE}/etl/run`, {
      method: "POST",
    });
    if (!response.ok) throw new Error("Falha ao executar ETL");
    await fetchInsights();
    setStatus("Insights atualizados minutos atrás.", "success");
  } catch (error) {
    console.error(error);
    setStatus("Erro ao executar ETL. Verifique o backend.", "error");
  } finally {
    triggerButton.disabled = false;
  }
};

triggerButton.addEventListener("click", triggerEtl);
fetchInsights();
