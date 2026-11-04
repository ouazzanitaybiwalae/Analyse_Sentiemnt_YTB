const $ = (s) => document.querySelector(s);
const SENT = {
  positive: { label: "positifs", cls: "pos", fr: "Positif" },
  neutral:  { label: "neutres",  cls: "neu", fr: "Neutre" },
  negative: { label: "négatifs", cls: "neg", fr: "Négatif" },
};
const PAGE = 50;
let data = { title: "", predictions: [], stats: null, ms: 0 };
let filter = "all", shown = PAGE;

// ---------- préférences (thème, serveur)
chrome.storage.local.get({ theme: "light", api: "cloud" }, (p) => {
  document.documentElement.dataset.theme = p.theme;
  $("#apiSel").value = p.api;
});
$("#themeBtn").onclick = () => {
  const t = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = t;
  chrome.storage.local.set({ theme: t });
};
$("#apiSel").onchange = (e) => chrome.storage.local.set({ api: e.target.value });

// ---------- états
function setStatus(msg, kind = "") {
  const el = $("#status");
  el.hidden = !msg; el.className = kind; el.textContent = "";
  if (kind === "loading") { const s = document.createElement("span"); s.className = "spinner"; el.append(s); }
  el.append(document.createTextNode(msg || ""));
}

// ---------- extraction
async function getComments(tab) {
  const options = { max: +$("#maxSel").value, includeReplies: $("#repliesChk").checked };
  const ask = () => chrome.tabs.sendMessage(tab.id, { type: "EXTRACT_COMMENTS", options });
  try { return await ask(); }
  catch { // onglet ouvert avant l'installation : on injecte le script
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
    return await ask();
  }
}

// ---------- API (par batch, avec timeout)
async function callApi(texts) {
  const { api } = await chrome.storage.local.get({ api: "cloud" });
  const base = API_TARGETS[api];
  const all = []; let ms = 0;
  for (let i = 0; i < texts.length; i += BATCH_SIZE) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), REQUEST_TIMEOUT);
    try {
      const r = await fetch(`${base}/predict_batch`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comments: texts.slice(i, i + BATCH_SIZE) }), signal: ctrl.signal,
      });
      if (!r.ok) throw new Error(`Erreur API (${r.status})`);
      const j = await r.json();
      j.predictions.forEach((p) => all.push(p));
      ms += j.processing_ms;
    } finally { clearTimeout(timer); }
  }
  return { predictions: all, ms };
}

function computeStats(preds) {
  const counts = { positive: 0, neutral: 0, negative: 0 };
  let conf = 0;
  preds.forEach((p) => { counts[p.sentiment]++; conf += p.confidence; });
  const n = preds.length || 1;
  const pct = Object.fromEntries(Object.entries(counts).map(([k, v]) => [k, +(v / n * 100).toFixed(1)]));
  return { total: preds.length, counts, pct, avgConf: conf / n };
}

// ---------- analyse
$("#analyzeBtn").onclick = async () => {
  const btn = $("#analyzeBtn");
  $("#results").hidden = true;
  btn.disabled = true;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.url?.includes("youtube.com/watch")) throw new Error("Ouvrez une vidéo YouTube (youtube.com/watch) puis réessayez.");
    setStatus("Extraction des commentaires… (défilement de la page)", "loading");
    const ex = await getComments(tab);
    if (!ex?.ok) throw new Error("Impossible de lire la page. Rechargez l'onglet YouTube.");
    if (!ex.comments.length) throw new Error("Aucun commentaire trouvé. Vérifiez que les commentaires sont activés.");

    setStatus(`Analyse de ${ex.comments.length} commentaires…`, "loading");
    const t0 = performance.now();
    const { predictions, ms } = await callApi(ex.comments.map((c) => c.text));
    predictions.forEach((p, i) => (p.isReply = ex.comments[i].isReply));
    data = { title: ex.title, predictions, stats: computeStats(predictions), ms, roundtrip: performance.now() - t0 };
    filter = "all"; shown = PAGE;
    setStatus("");
    render();
  } catch (e) {
    const net = e.name === "AbortError" || e instanceof TypeError;
    setStatus(net ? "Serveur injoignable. Vérifiez l'URL dans config.js, ou patientez si le Space se réveille, puis réessayez." : e.message, "error");
  } finally { btn.disabled = false; }
};

// ---------- affichage
function render() {
  const { stats } = data;
  const top = Object.keys(stats.pct).reduce((a, b) => (stats.pct[a] >= stats.pct[b] ? a : b));
  $("#topPct").textContent = Math.round(stats.pct[top]);
  $("#topLabel").textContent = SENT[top].label;

  const bar = $("#bar"); bar.textContent = "";
  const legend = $("#legend"); legend.textContent = "";
  for (const k of ["positive", "neutral", "negative"]) {
    const seg = document.createElement("span");
    seg.className = SENT[k].cls; seg.style.width = stats.pct[k] + "%"; seg.title = `${SENT[k].fr} ${stats.pct[k]}%`;
    bar.append(seg);
    const li = document.createElement("li");
    const dot = document.createElement("i"); dot.className = "dot " + SENT[k].cls;
    li.append(dot, `${SENT[k].fr} ${stats.pct[k]}% (${stats.counts[k]})`);
    legend.append(li);
  }
  $("#meta").textContent = `${stats.total} commentaires · confiance moyenne ${(stats.avgConf * 100).toFixed(0)}% · modèle ${data.ms.toFixed(0)} ms · total ${data.roundtrip.toFixed(0)} ms`;
  renderList();
  $("#results").hidden = false;
}

function renderList() {
  const items = data.predictions.filter((p) => filter === "all" || p.sentiment === filter);
  const list = $("#list"); list.textContent = "";
  if (!items.length) {
    const li = document.createElement("li"); li.className = "empty"; li.textContent = "Aucun commentaire dans cette catégorie."; list.append(li);
  }
  // rendu progressif : 50 éléments à la fois pour rester fluide avec beaucoup de commentaires
  const frag = document.createDocumentFragment();
  items.slice(0, shown).forEach((p) => {
    const li = document.createElement("li"); if (p.isReply) li.className = "reply";
    const dot = document.createElement("i"); dot.className = "dot " + SENT[p.sentiment].cls; dot.style.marginTop = "5px"; dot.title = SENT[p.sentiment].fr;
    const txt = document.createElement("span"); txt.className = "txt"; txt.textContent = p.text;
    const conf = document.createElement("span"); conf.className = "conf"; conf.textContent = Math.round(p.confidence * 100) + "%";
    li.append(dot, txt, conf); frag.append(li);
  });
  list.append(frag);
  $("#moreBtn").hidden = items.length <= shown;
}

$("#filters").onclick = (e) => {
  const b = e.target.closest(".chip"); if (!b) return;
  document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c === b));
  filter = b.dataset.f; shown = PAGE; renderList();
};
$("#moreBtn").onclick = () => { shown += PAGE; renderList(); };

// ---------- export
function asText() {
  const s = data.stats;
  const head = `Analyse de sentiment : ${data.title}\n${s.total} commentaires | Positif ${s.pct.positive}% | Neutre ${s.pct.neutral}% | Négatif ${s.pct.negative}%\n\n`;
  return head + data.predictions.map((p) => `[${SENT[p.sentiment].fr} ${Math.round(p.confidence * 100)}%] ${p.text}`).join("\n");
}
$("#copyBtn").onclick = async (e) => {
  await navigator.clipboard.writeText(asText());
  e.target.textContent = "Copié !"; setTimeout(() => (e.target.textContent = "Copier les résultats"), 1500);
};
$("#csvBtn").onclick = () => {
  const esc = (t) => `"${t.replace(/"/g, '""')}"`;
  const csv = "sentiment,confidence,text\n" + data.predictions.map((p) => `${p.sentiment},${p.confidence},${esc(p.text)}`).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }));
  a.download = "youtube_sentiment.csv"; a.click(); URL.revokeObjectURL(a.href);
};
