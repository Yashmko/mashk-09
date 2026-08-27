const state = { summary: null, rounds: [], running: false };
const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}
function formatPercent(value) { return `${Math.round((value || 0) * 100)}%`; }
function formatTime(value) { return value ? `${value}s` : "—"; }
async function getJson(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error((await response.json()).detail || `Request failed: ${response.status}`);
  return response.json();
}

function renderMetrics(summary) {
  $("#metric-rounds").textContent = summary.total_rounds;
  $("#metric-red").textContent = formatPercent(summary.red_win_rate);
  $("#metric-detect").textContent = formatPercent(summary.blue_detection_rate);
  $("#metric-time").textContent = formatTime(summary.average_detection_seconds);
  const latest = summary.history.at(-1);
  $("#stage-generation").textContent = latest ? `gen ${String(latest.generation).padStart(2, "0")}` : "gen 00";
  $("#stage-red").textContent = latest ? `${latest.red_score} / 100` : "standby";
  $("#stage-blue").textContent = latest ? `${latest.blue_score} / 100` : "standby";
  $("#chart-range").textContent = summary.total_rounds ? `G01 — G${String(summary.total_rounds).padStart(2, "0")}` : "awaiting history";
}

function renderChart(history) {
  const svg = $("#trend-chart");
  const empty = $("#chart-empty");
  if (!history.length) { svg.innerHTML = ""; empty.style.display = "grid"; return; }
  empty.style.display = "none";
  const width = 900, height = 340, pad = { top: 25, right: 24, bottom: 45, left: 42 };
  const innerW = width - pad.left - pad.right, innerH = height - pad.top - pad.bottom;
  const x = (index) => pad.left + (history.length === 1 ? innerW / 2 : (index / (history.length - 1)) * innerW);
  const y = (value) => pad.top + innerH - (value / 100) * innerH;
  const line = (key) => history.map((item, index) => `${index ? "L" : "M"}${x(index).toFixed(1)},${y(item[key]).toFixed(1)}`).join(" ");
  const area = (key) => `${line(key)} L ${x(history.length - 1)},${height - pad.bottom} L ${x(0)},${height - pad.bottom} Z`;
  const grid = [0, 25, 50, 75, 100].map((value) => `<line class="grid-line" x1="${pad.left}" x2="${width - pad.right}" y1="${y(value)}" y2="${y(value)}"/><text class="axis-label" x="6" y="${y(value) + 4}">${value}</text>`).join("");
  const labels = history.map((item, index) => `<text class="axis-label x-label" x="${x(index)}" y="${height - 13}">G${String(item.generation).padStart(2, "0")}</text>`).join("");
  const points = (key, cls) => history.map((item, index) => `<circle class="point ${cls}" cx="${x(index)}" cy="${y(item[key])}" r="4"><title>Generation ${item.generation}: ${item[key]}</title></circle>`).join("");
  svg.innerHTML = `<defs><linearGradient id="red-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#f36f62" stop-opacity=".22"/><stop offset="1" stop-color="#f36f62" stop-opacity="0"/></linearGradient><linearGradient id="blue-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#78e8e1" stop-opacity=".18"/><stop offset="1" stop-color="#78e8e1" stop-opacity="0"/></linearGradient></defs>${grid}${labels}<path class="area-fill red-fill" d="${area("red_score")}"/><path class="area-fill blue-fill" d="${area("blue_score")}"/><path class="trend-line red-line" d="${line("red_score")}"/><path class="trend-line blue-line" d="${line("blue_score")}"/>${points("red_score", "red-point")}${points("blue_score", "blue-point")}`;
}

function renderPlaybook(id, playbook, color) {
  const priority = playbook.priority || [], blocked = playbook.blocked_patterns || [];
  const values = [...priority.map((value) => ({ value, type: color })), ...blocked.map((value) => ({ value, type: "blocked" }))].slice(0, 7);
  $(id).innerHTML = values.length ? values.map(({ value, type }) => `<span class="playbook-chip ${type}">${escapeHtml(value)}</span>`).join("") : '<span class="muted">No memory yet.</span>';
}

function renderTechniques(techniques) {
  $("#technique-count").textContent = techniques.length;
  $("#techniques").innerHTML = techniques.length ? techniques.map((item, index) => `<div class="technique-row"><div class="technique-index">${String(index + 1).padStart(2, "0")}</div><div><div class="technique-topline"><strong>${escapeHtml(item.name)}</strong><span>G${item.first_seen_generation}</span></div><small>${escapeHtml(item.technique_id)} · ${escapeHtml(item.description)}</small></div></div>`).join("") : '<div class="empty-state">No novel techniques observed.</div>';
}

function renderTimeline(round) {
  $("#timeline").innerHTML = round ? `<div class="timeline-summary"><span>GENERATION ${String(round.generation).padStart(2, "0")}</span><strong>${round.red_win ? "RED PRESSURE HELD" : "BLUE RESPONSE HELD"}</strong><span>${round.events.length} events</span></div>${round.events.map((event) => `<div class="timeline-event ${event.actor}"><div class="event-marker"></div><div class="event-body"><div class="event-meta"><span>${escapeHtml(event.actor.toUpperCase())}</span><span>SEQ ${String(event.sequence).padStart(2, "0")}</span><span class="event-outcome ${event.outcome}">${escapeHtml(event.outcome.toUpperCase())}</span></div><strong>${escapeHtml(event.action)} <span class="target">→ ${escapeHtml(event.target)}</span></strong><p>${escapeHtml(event.detail)}</p></div></div>`).join("")}` : '<div class="empty-state">The event stream will appear here after a round.</div>';
}

function renderSelect(rounds) {
  const select = $("#generation-select");
  select.innerHTML = rounds.length ? rounds.map((round) => `<option value="${round.generation}">Generation ${String(round.generation).padStart(2, "0")}</option>`).join("") : '<option value="">no rounds</option>';
  if (rounds.length) select.value = rounds[0].generation;
}

async function refresh(preferredGeneration) {
  state.summary = await getJson("/api/summary");
  state.rounds = await getJson("/api/rounds?limit=100");
  renderMetrics(state.summary); renderChart(state.summary.history); renderTechniques(state.summary.novel_techniques);
  const playbook = await getJson("/api/playbook");
  renderPlaybook("#red-playbook", playbook.red, "red"); renderPlaybook("#blue-playbook", playbook.blue, "blue");
  renderSelect(state.rounds);
  const generation = preferredGeneration || (state.rounds[0] && state.rounds[0].generation);
  if (generation) { $("#generation-select").value = generation; renderTimeline(state.rounds.find((round) => round.generation === Number(generation))); }
}

async function runSimulation() {
  if (state.running) return;
  const count = Math.min(25, Math.max(1, Number($("#round-count").value || 1)));
  state.running = true;
  const button = $("#run-rounds");
  button.classList.add("is-running"); button.disabled = true;
  $("#run-status").innerHTML = '<span class="status-bullet spinning"></span> running synthetic generation loop...';
  try {
    const result = await getJson("/api/rounds", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ count }) });
    await refresh(result.latest.generation);
    $("#run-status").innerHTML = `<span class="status-bullet"></span> generation ${String(result.latest.generation).padStart(2, "0")} committed to lineage memory`;
  } catch (error) { $("#run-status").innerHTML = `<span class="status-bullet danger"></span> ${escapeHtml(error.message)}`; }
  finally { state.running = false; button.classList.remove("is-running"); button.disabled = false; }
}

$("#run-rounds").addEventListener("click", runSimulation);
$("#generation-select").addEventListener("change", (event) => { const round = state.rounds.find((item) => item.generation === Number(event.target.value)); renderTimeline(round); });
$("#theme-button").addEventListener("click", () => document.body.classList.toggle("low-glow"));
document.addEventListener("keydown", (event) => { if ((event.metaKey || event.ctrlKey) && event.key === "Enter") runSimulation(); });
document.addEventListener("pointermove", (event) => { const stage = $(".world-stage"); if (!stage) return; const rect = stage.getBoundingClientRect(); stage.style.setProperty("--mouse-x", `${((event.clientX - rect.left) / rect.width) * 100}%`); stage.style.setProperty("--mouse-y", `${((event.clientY - rect.top) / rect.height) * 100}%`); });
function tick() { $("#clock").textContent = `${new Date().toISOString().slice(11, 19)} UTC`; }
tick(); setInterval(tick, 1000); refresh().catch((error) => { $("#run-status").innerHTML = `<span class="status-bullet danger"></span> API unavailable: ${escapeHtml(error.message)}`; });
