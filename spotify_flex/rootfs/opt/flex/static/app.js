/* Spotify Flex app UI – vanilla JS, served through Home Assistant ingress (relative URLs only). */
"use strict";

const ICON = {
  play: "M8 5v14l11-7z",
  pause: "M6 5h4v14H6zm8 0h4v14h-4z",
  next: "M6 18l8.5-6L6 6v12zm10-12v12h2V6h-2z",
  prev: "M6 6h2v12H6zm3.5 6l8.5 6V6z",
  shuffle: "M10.6 9.2 5.4 4 4 5.4l5.2 5.2 1.4-1.4zM14.5 4l2 2L4 18.6 5.4 20 18 7.5l2 2V4h-5.5zm.3 9.4-1.4 1.4 3.1 3.1-2 2.1H20v-5.5l-2 2-3.2-3.1z",
  repeat: "M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z",
  repeatOne: "M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z",
  heart: "M12 21.4 10.6 20C5.4 15.4 2 12.3 2 8.5 2 5.4 4.4 3 7.5 3c1.7 0 3.4.8 4.5 2.1C13.1 3.8 14.8 3 16.5 3 19.6 3 22 5.4 22 8.5c0 3.8-3.4 6.9-8.6 11.5L12 21.4z",
  heartO: "M16.5 3c-1.7 0-3.4.8-4.5 2.1C10.9 3.8 9.2 3 7.5 3 4.4 3 2 5.4 2 8.5c0 3.8 3.4 6.9 8.6 11.5L12 21.4l1.4-1.3C18.6 15.4 22 12.3 22 8.5 22 5.4 19.6 3 16.5 3zm-4.4 15.6-.1.1-.1-.1C7.1 14.2 4 11.4 4 8.5 4 6.5 5.5 5 7.5 5c1.5 0 3 1 3.6 2.4h1.9C13.5 6 15 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.9-3.1 5.7-7.9 10.1z",
  more: "M12 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm0 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm0 6a2 2 0 1 0 0 4 2 2 0 0 0 0-4z",
  back: "M20 11H7.8l5.6-5.6L12 4l-8 8 8 8 1.4-1.4L7.8 13H20z",
  chevron: "M9.3 6.7 10.7 5.3 17.4 12l-6.7 6.7-1.4-1.4 5.3-5.3z",
  note: "M12 3v10.6A4 4 0 1 0 14 17V7h4V3h-6z",
  speaker: "M17 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2zm-5 2a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm0 16a5 5 0 1 1 0-10 5 5 0 0 1 0 10zm0-8a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
  volLow: "M7 9v6h4l5 5V4l-5 5H7z",
  volHigh: "M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0 0 14 8v8a4.5 4.5 0 0 0 2.5-4zM14 3.2v2.1a7 7 0 0 1 0 13.4v2.1a9 9 0 0 0 0-17.6z",
  queue: "M3 6h12v2H3zm0 4h12v2H3zm0 4h8v2H3zm14-2v-4h-2v4h-4v2h4v4h2v-4h4v-2z",
  add: "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6z",
  remove: "M19 6.4 17.6 5 12 10.6 6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12z",
  up: "M7.4 15.4 12 10.8l4.6 4.6L18 14l-6-6-6 6z",
  down: "M7.4 8.6 12 13.2l4.6-4.6L18 10l-6 6-6-6z",
  trash: "M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
  power: "M13 3h-2v10h2V3zm4.8 2.2-1.4 1.4A6.9 6.9 0 0 1 19 12a7 7 0 1 1-11.4-5.4L6.2 5.2A9 9 0 1 0 21 12a8.9 8.9 0 0 0-3.2-6.8z",
  edit: "M3 17.2V21h3.8l11-11-3.8-3.8-11 11zM20.7 7a1 1 0 0 0 0-1.4l-2.3-2.3a1 1 0 0 0-1.4 0l-1.8 1.8 3.7 3.8L20.7 7z",
  open: "M14 3v2h3.6l-9.8 9.8 1.4 1.4L19 6.4V10h2V3h-7zm5 16H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7h-2v7z",
  loading: "M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z",
  device: "M4 6h18V4H4a2 2 0 0 0-2 2v11H0v3h14v-3H4V6zm19 2h-6a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1zm-1 9h-4v-7h4v7z",
};
const svg = (name) => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${ICON[name] || ICON.note}"/></svg>`;
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (ms) => { const s = Math.max(0, Math.floor((ms || 0) / 1000)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };
const $ = (sel) => document.querySelector(sel);

const TABS = [
  { node: "playlists", label: "Playlists" },
  { node: "liked", label: "Lieblingssongs" },
  { node: "albums", label: "Alben" },
  { node: "artists", label: "Künstler" },
  { node: "recent", label: "Zuletzt gehört" },
  { node: "shows", label: "Podcasts" },
  { node: "root", label: "Mehr" },
];

const S = {
  state: null, player: null, receivedAt: 0, speakers: [], groups: [], activeGroup: null, tab: "playlists", stack: [],
  page: null, loading: false, error: null, query: "", liked: null, busy: new Set(), showSetup: false,
};

/* ------------------------------------------------------------------ api */
async function api(path, { method = "GET", body } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30000);
  try {
    const res = await fetch(path, {
      method, signal: ctrl.signal, credentials: "same-origin",
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    let data = null;
    try { data = await res.json(); } catch (_) { /* empty */ }
    if (!res.ok) throw Object.assign(new Error((data && data.error) || `Fehler ${res.status}`), { status: res.status });
    return data;
  } catch (err) {
    if (err.name === "AbortError") throw new Error("Zeitüberschreitung – bitte erneut versuchen.");
    throw err;
  } finally { clearTimeout(timer); }
}

async function once(key, fn) {
  if (S.busy.has(key)) return;
  S.busy.add(key);
  try { return await fn(); } catch (err) { toast(err.message, true); } finally { S.busy.delete(key); }
}

let toastTimer;
function toast(text, err = false) {
  const el = $("#toast");
  el.textContent = text;
  el.className = "toast" + (err ? " err" : "");
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, err ? 8000 : 3500);
}

/* ------------------------------------------------------------- state */
async function loadState() {
  try {
    S.state = await api("api/state");
    S.speakers = S.state.speakers || [];
    S.groups = S.state.groups || []; S.activeGroup = S.state.active_group || null;
    setPlayer(S.state.player);
  } catch (err) {
    S.state = null;
  }
  renderPills();
  const typing = (sel) => document.activeElement && document.activeElement.closest && document.activeElement.closest(sel);
  if (!typing("#setup") && !($("#web-paste") && $("#web-paste").value)) renderSetup();
  if (!typing("#speakers")) renderSpeakers();
}

function setPlayer(p) {
  S.player = p; S.receivedAt = Date.now();
  renderNow();
  refreshLiked();
}

let lastLikedUri = null;
async function refreshLiked() {
  const uri = S.player && S.player.track && S.player.track.uri;
  if (!uri || uri === lastLikedUri || !(S.state && S.state.web.connected)) return;
  lastLikedUri = uri;
  try { S.liked = (await api("api/now/liked")).liked; } catch (_) { S.liked = null; }
  renderNow();
}

function connectWs() {
  const url = location.href.replace(/^http/, "ws").replace(/[#?].*$/, "").replace(/\/[^/]*$/, "/") + "ws";
  let ws;
  try { ws = new WebSocket(url); } catch (_) { setTimeout(connectWs, 5000); return; }
  ws.onmessage = (ev) => {
    try { const m = JSON.parse(ev.data); if (m.type === "status") setPlayer(m.data); else if (m.type === "speakers") applySpeakers(m.data); } catch (_) { /* ignore */ }
  };
  ws.onclose = () => setTimeout(connectWs, 4000);
}

/* ------------------------------------------------------------- header + setup */
function renderPills() {
  const st = S.state;
  const r = $("#pill-receiver"), w = $("#pill-web");
  const recOk = st && st.receiver.logged_in, webOk = st && st.web.connected;
  r.className = "pill " + (recOk ? "ok" : "bad"); r.textContent = recOk ? "Empfänger bereit" : "Empfänger: Anmeldung nötig";
  w.className = "pill " + (webOk ? "ok" : "bad"); w.textContent = webOk ? "Bibliothek verbunden" : "Bibliothek: Anmeldung nötig";
}

function renderSetup() {
  const el = $("#setup");
  const st = S.state;
  if (!st) { el.hidden = false; el.innerHTML = `<h2>Spotify Flex startet …</h2><p class="hint">Die Dienste der App starten gerade. Diese Seite aktualisiert sich selbst.</p>`; return; }
  const recOk = st.receiver.logged_in, webOk = st.web.connected, spkOk = S.speakers.some((s) => s.selected);
  if (recOk && webOk && !S.showSetup) { el.hidden = true; return; }
  el.hidden = false;
  const code = st.receiver.auth_code;
  const rec = recOk
    ? `<p class="hint">Angemeldet${S.player && S.player.username ? ` als <b>${esc(S.player.username)}</b>` : ""}. Der Empfänger heißt „${esc((S.player && S.player.device_name) || "Home Flex")}“.</p>
       <div class="btn-row"><button class="btn" data-act="receiver-logout">Empfänger abmelden</button></div>`
    : code
      ? `<p class="hint">Öffne auf Handy oder PC diesen Link und bestätige mit deinem Spotify-Konto. Falls nach einem Code gefragt wird:</p>
         <div class="code">${esc(code.code)}</div>
         <div class="btn-row"><a class="btn primary" href="${esc(code.url)}" target="_blank" rel="noopener">Bei Spotify bestätigen</a></div>
         <p class="hint">Gültig bis ${esc(new Date(code.expires_at).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }))} Uhr. Danach erscheint automatisch ein neuer Code.</p>`
      : st.receiver.running
        ? `<p class="hint">Warte auf den Anmeldecode von Spotify …</p>`
        : `<p class="hint err">Der Empfänger läuft nicht. Prüfe das Protokoll der App.</p>`;
  let web;
  if (webOk) {
    web = `<p class="hint">Bibliothek, Playlists und Suche sind verbunden.</p><div class="btn-row"><button class="btn" data-act="web-logout">Bibliothek trennen</button></div>`;
  } else if (!st.web.configured) {
    web = `<p class="hint">Trage in Home Assistant unter <b>Einstellungen → Apps → Spotify Flex → Konfiguration</b> die <b>Client-ID</b> deiner Spotify-Entwickler-App ein und starte die App neu. Ein Client-Secret ist nicht nötig.</p>`;
  } else {
    web = `<p class="hint">1. Im <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener">Spotify-Entwickler-Dashboard</a> bei deiner App unter <i>Redirect URIs</i> diese Adresse ergänzen und speichern:<br><code class="inline">${esc(st.web.redirect_uri)}</code></p>
      <p class="hint">2. Anmelden. Danach landest du auf einer Seite, die nicht lädt – das ist richtig.</p>
      <div class="btn-row"><button class="btn primary" data-act="web-login">Mit Spotify anmelden</button></div>
      <p class="hint">3. Die komplette Adresse dieser Seite (beginnt mit <code class="inline">http://127.0.0.1:8765/callback?code=</code>) hier einfügen:</p>
      <input class="field" id="web-paste" placeholder="http://127.0.0.1:8765/callback?code=…">
      <div class="btn-row"><button class="btn primary" data-act="web-finish">Übernehmen</button></div>`;
  }
  el.innerHTML = `<h2><span class="sp">Einrichtung</span>${recOk && webOk ? `<button class="btn" data-act="close-setup">Schließen</button>` : ""}</h2>
    <div class="step ${recOk ? "done" : ""}"><div class="num">1</div><div><b>Spotify-Empfänger anmelden</b>${rec}</div></div>
    <div class="step ${webOk ? "done" : ""}"><div class="num">2</div><div><b>Bibliothek verbinden</b>${web}</div></div>
    <div class="step ${spkOk ? "done" : ""}"><div class="num">3</div><div><b>Lautsprecher wählen</b><p class="hint">${spkOk ? "Mindestens ein Lautsprecher ist aktiv." : "Schalte unten bei „Lautsprecher“ deine HomePods ein."}</p></div></div>`;
}

$("#setup").addEventListener("click", async (ev) => {
  const act = ev.target.closest("[data-act]")?.dataset.act;
  if (!act) return;
  if (act === "close-setup") { S.showSetup = false; renderSetup(); }
  if (act === "web-login") await once("login", async () => { const r = await api("api/web/authorize", { method: "POST" }); window.open(r.url, "_blank", "noopener"); });
  if (act === "web-finish") await once("finish", async () => {
    const r = await api("api/web/finish", { method: "POST", body: { url: $("#web-paste").value } });
    toast(`Bibliothek verbunden${r.name ? ` (${r.name})` : ""}.`); await loadState(); openNode(S.tab, true);
  });
  if (act === "web-logout") await once("wlo", async () => { await api("api/web/logout", { method: "POST" }); await loadState(); });
  if (act === "receiver-logout" && confirm("Empfänger wirklich von Spotify abmelden?")) await once("rlo", async () => { await api("api/receiver/logout", { method: "POST" }); setTimeout(loadState, 3000); });
});

$("#btn-settings").addEventListener("click", () => openSettings());

/* ------------------------------------------------------------- now playing */
function position() {
  const p = S.player, t = p && p.track;
  if (!t) return 0;
  let pos = t.position_ms || 0;
  if (p.playing) pos += Date.now() - S.receivedAt;
  return Math.min(pos, t.duration_ms || pos);
}

function renderNow() {
  const el = $("#now");
  const p = S.player || {}, t = p.track;
  const repeatIcon = p.repeat === "track" ? "repeatOne" : "repeat";
  el.innerHTML = `
    <div class="cover-well">${t && t.image ? `<img src="${esc(t.image)}" alt="">` : `<div class="ph">${svg("note")}</div>`}</div>
    <div class="meta">
      <div style="min-width:0"><div class="t">${esc(t ? t.name : "Nichts läuft")}</div><div class="a">${esc(t ? t.artists : (p.online ? "Wähle rechts etwas aus deiner Bibliothek" : "Empfänger nicht verbunden"))}</div></div>
      ${t ? `<button class="icon-btn ${S.liked ? "on" : ""}" data-act="like" aria-label="${S.liked ? "Aus Lieblingssongs entfernen" : "Zu Lieblingssongs"}">${svg(S.liked ? "heart" : "heartO")}</button>` : ""}
    </div>
    <div class="groove" data-act="seek" role="slider" aria-label="Position"><div class="fill"></div></div>
    <div class="times"><span id="pos">0:00</span><span>${fmt(t && t.duration_ms)}</span></div>
    <div class="controls">
      <button class="icon-btn ${p.shuffle ? "on" : ""}" data-act="shuffle" aria-label="Zufall" aria-pressed="${!!p.shuffle}">${svg("shuffle")}</button>
      <button class="icon-btn" data-act="prev" aria-label="Zurück">${svg("prev")}</button>
      <button class="icon-btn play" data-act="playpause" aria-label="${p.playing ? "Pause" : "Abspielen"}">${svg(p.playing ? "pause" : "play")}</button>
      <button class="icon-btn" data-act="next" aria-label="Weiter">${svg("next")}</button>
      <button class="icon-btn ${p.repeat && p.repeat !== "off" ? "on" : ""}" data-act="repeat" aria-label="Wiederholen">${svg(repeatIcon)}</button>
    </div>
    <div class="range">${svg("volLow")}<input type="range" min="0" max="100" value="${p.volume ?? 50}" data-act="volume" aria-label="Lautstärke">${svg("volHigh")}</div>`;
  tick();
}

function tick() {
  const fill = document.querySelector("#now .fill"), pos = $("#pos");
  const t = S.player && S.player.track;
  if (!fill) return;
  const cur = position();
  fill.style.width = t && t.duration_ms ? `${Math.min(100, (cur / t.duration_ms) * 100)}%` : "0%";
  if (pos) pos.textContent = fmt(cur);
}
setInterval(tick, 1000);

async function player(action, body) {
  return once("player:" + action, async () => {
    const r = await api(`api/player/${action}`, { method: "POST", body: body || {} });
    if (r && r.player) setPlayer(r.player);
  });
}

$("#now").addEventListener("click", async (ev) => {
  const el = ev.target.closest("[data-act]");
  if (!el) return;
  const p = S.player || {};
  switch (el.dataset.act) {
    case "playpause": return player("playpause");
    case "prev": return player("prev");
    case "next": return player("next");
    case "shuffle": return player("shuffle", { on: !p.shuffle });
    case "repeat": return player("repeat", { mode: p.repeat === "off" ? "context" : p.repeat === "context" ? "track" : "off" });
    case "like": return once("like", async () => {
      const uri = p.track && p.track.uri;
      await api("api/library", { method: "POST", body: { action: S.liked ? "remove" : "save", uris: [uri] } });
      S.liked = !S.liked; renderNow(); toast(S.liked ? "Zu Lieblingssongs hinzugefügt." : "Aus Lieblingssongs entfernt.");
    });
    case "seek": {
      const t = p.track; if (!t || !t.duration_ms) return;
      const r = el.getBoundingClientRect();
      return player("seek", { position_ms: Math.round(Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)) * t.duration_ms) });
    }
  }
});
$("#now").addEventListener("change", (ev) => { if (ev.target.dataset.act === "volume") player("volume", { percent: Number(ev.target.value) }); });

/* ------------------------------------------------------------- speakers */
function applySpeakers(d) {
  if (!d) return;
  if (d.speakers) S.speakers = d.speakers;
  if (d.groups) S.groups = d.groups;
  S.activeGroup = d.active_group || null;
  const typing = document.activeElement && document.activeElement.closest && document.activeElement.closest("#speakers");
  if (!typing) renderSpeakers();
  renderSetup();
}

function renderGroups() {
  const selected = S.speakers.filter((s) => s.selected);
  const names = (g) => g.speakers.map((id) => (S.speakers.find((s) => s.id === id) || {}).name).filter(Boolean).join(", ");
  const chips = S.groups.map((g) => `
    <div class="gchip ${g.id === S.activeGroup ? "sel" : ""}" data-gid="${esc(g.id)}">
      <button class="gname" data-act="grp-on" title="${esc(names(g) || "Lautsprecher derzeit nicht gefunden")}">${esc(g.name)}<small>${g.speakers.length}</small></button>
      <button class="gx" data-act="grp-menu" aria-label="Gruppe ${esc(g.name)} bearbeiten">${svg("more")}</button>
    </div>`).join("");
  const canSave = selected.length > 0 && !S.activeGroup;
  return `<div class="groups">${chips}${canSave ? `<button class="gadd" data-act="grp-save">+ Auswahl als Gruppe</button>` : ""}</div>
    ${!S.groups.length && !canSave ? `<p class="hint small">Tipp: mehrere Lautsprecher einschalten und als Gruppe speichern.</p>` : ""}`;
}

function renderSpeakers() {
  const el = $("#speakers");
  const err = S.state && S.state.speaker_error;
  const rows = S.speakers.map((s) => `
    <div class="spk" data-id="${esc(s.id)}">
      <div class="n">${esc(s.name)}</div>
      <button class="switch" role="switch" aria-checked="${s.selected}" data-act="toggle" aria-label="${esc(s.name)} ${s.selected ? "ausschalten" : "einschalten"}"></button>
      ${s.selected ? `<div class="range">${svg("volLow")}<input type="range" min="0" max="100" value="${s.volume ?? 50}" data-act="spk-vol" aria-label="Lautstärke ${esc(s.name)}">${svg("volHigh")}</div>` : ""}
    </div>`).join("");
  el.innerHTML = `<h2>${svg("speaker")}<span class="sp">Lautsprecher</span><button class="icon-btn" data-act="spk-off" aria-label="Alle Lautsprecher aus">${svg("power")}</button><button class="icon-btn" data-act="spk-refresh" aria-label="Lautsprecher neu suchen">${svg("loading")}</button></h2>
    ${S.speakers.length ? renderGroups() : ""}
    ${rows || `<p class="hint ${err ? "err" : ""}">${esc(err || "Noch keine AirPlay-Lautsprecher gefunden. HomePods müssen im selben Netz und eingeschaltet sein; die Suche läuft automatisch.")}</p>`}`;
}

$("#speakers").addEventListener("click", async (ev) => {
  const act = ev.target.closest("[data-act]")?.dataset.act;
  if (act === "spk-refresh") return once("spk", async () => { S.speakers = (await api("api/speakers")).speakers; renderSpeakers(); renderSetup(); });
  if (act === "spk-off") return once("spk", async () => applySpeakers(await api("api/speakers", { method: "POST", body: { speakers: [] } })));
  if (act === "grp-save") {
    const ids = S.speakers.filter((s) => s.selected).map((s) => s.id);
    const name = prompt("Name der Gruppe (z. B. Erdgeschoss, Überall):");
    if (!name) return;
    return once("grp", async () => { applySpeakers(await api("api/groups", { method: "POST", body: { name, speakers: ids } })); toast(`Gruppe „${name}“ gespeichert`); });
  }
  if (act === "grp-on") {
    const gid = ev.target.closest(".gchip").dataset.gid;
    return once("grp", async () => { const r = await api(`api/groups/${encodeURIComponent(gid)}/activate`, { method: "POST", body: {} }); applySpeakers(r); if (r.warning) toast(r.warning, true); });
  }
  if (act === "grp-menu") {
    const g = S.groups.find((x) => x.id === ev.target.closest(".gchip").dataset.gid);
    if (!g) return;
    const card = sheet(`<h3>Gruppe „${esc(g.name)}“</h3>
      <div class="list">
        <button class="row" style="grid-template-columns:48px 1fr" data-gact="update"><span class="ic">${svg("speaker")}</span><span class="t"><span class="n">Aktuelle Auswahl übernehmen</span><span class="s">${esc(S.speakers.filter((s) => s.selected).map((s) => s.name).join(", ") || "– nichts eingeschaltet –")}</span></span></button>
        <button class="row" style="grid-template-columns:48px 1fr" data-gact="rename"><span class="ic">${svg("edit")}</span><span class="t"><span class="n">Umbenennen</span></span></button>
        <button class="row" style="grid-template-columns:48px 1fr" data-gact="delete"><span class="ic">${svg("trash")}</span><span class="t"><span class="n">Gruppe löschen</span></span></button>
      </div><div class="btn-row"><button class="btn" data-act="close">Schließen</button></div>`);
    card.onclick = (e) => {
      const gact = e.target.closest("[data-gact]")?.dataset.gact;
      if (!gact) return;
      const path = `api/groups/${encodeURIComponent(g.id)}`;
      once("grp", async () => {
        if (gact === "update") {
          const ids = S.speakers.filter((s) => s.selected).map((s) => s.id);
          applySpeakers(await api(path, { method: "PUT", body: { speakers: ids } }));
        } else if (gact === "rename") {
          const name = prompt("Neuer Name:", g.name);
          if (!name) return;
          applySpeakers(await api(path, { method: "PUT", body: { name } }));
        } else if (gact === "delete") {
          if (!confirm(`Gruppe „${g.name}“ löschen?`)) return;
          applySpeakers(await api(path, { method: "DELETE" }));
        }
        closeSheet();
      });
    };
    return;
  }
  if (act !== "toggle") return;
  const id = ev.target.closest(".spk").dataset.id;
  const spk = S.speakers.find((s) => s.id === id);
  await once("spk:" + id, async () => {
    const body = { selected: !spk.selected };
    if (!spk.selected && spk.needs_pin) {
      const pin = prompt(`${spk.name} verlangt eine Bestätigung. Bitte die PIN eingeben, die der Lautsprecher anzeigt (bei HomePods meist nicht nötig – sonst in der Home-App „Lautsprecherzugriff: Alle im selben Netzwerk“ erlauben):`);
      if (pin) body.pin = pin;
    }
    applySpeakers(await api(`api/speakers/${encodeURIComponent(id)}`, { method: "POST", body }));
  });
});
$("#speakers").addEventListener("change", (ev) => {
  if (ev.target.dataset.act !== "spk-vol") return;
  const id = ev.target.closest(".spk").dataset.id;
  once("spkv:" + id, () => api(`api/speakers/${encodeURIComponent(id)}`, { method: "POST", body: { volume: Number(ev.target.value) } }));
});

/* ------------------------------------------------------------- library */
function renderTabs() {
  $("#tabs").innerHTML = TABS.map((t) => `<button class="tab ${S.tab === t.node ? "sel" : ""}" role="tab" aria-selected="${S.tab === t.node}" data-node="${t.node}">${t.label}</button>`).join("");
}
$("#tabs").addEventListener("click", (ev) => { const b = ev.target.closest(".tab"); if (b) openNode(b.dataset.node, true); });

let loadToken = 0;
async function openNode(node, reset = false, title = null) {
  if (reset) { S.tab = TABS.some((t) => t.node === node) ? node : S.tab; S.stack = []; renderTabs(); }
  S.stack.push({ node, title });
  await load(node, 0, false);
}

async function load(node, offset, append) {
  const token = ++loadToken;
  if (!(S.state && S.state.web.connected)) { S.page = null; S.error = "Bitte zuerst oben die Bibliothek verbinden."; S.loading = false; renderBrowser(); return; }
  S.loading = true; S.error = null; if (!append) S.page = null;
  renderBrowser();
  try {
    const res = await api(`api/browse?node=${encodeURIComponent(node)}&offset=${offset}`);
    if (token !== loadToken) return;
    S.page = append && S.page ? { ...res, items: [...S.page.items, ...res.items] } : res;
  } catch (err) {
    if (token !== loadToken) return;
    S.error = err.message;
  }
  S.loading = false; renderBrowser();
}

async function search(q) {
  const token = ++loadToken;
  S.query = q; S.stack = [{ node: "search", title: `Suche: ${q}` }];
  S.loading = true; S.error = null; S.page = null; renderBrowser();
  try {
    const res = await api(`api/search?q=${encodeURIComponent(q)}&types=track,album,artist,playlist,show`);
    if (token !== loadToken) return;
    const groups = [["tracks", "Titel"], ["artists", "Künstler"], ["albums", "Alben"], ["playlists", "Playlists"], ["shows", "Podcasts"]];
    const items = [];
    for (const [k, label] of groups) {
      const list = (res[k] && res[k].items) || [];
      if (list.length) { items.push({ group: label }); items.push(...list); }
    }
    S.page = { node: "search", title: `Suche: ${q}`, items, next_offset: null };
  } catch (err) { if (token === loadToken) S.error = err.message; }
  S.loading = false; renderBrowser();
}
$("#search").addEventListener("submit", (ev) => { ev.preventDefault(); const q = $("#search-q").value.trim(); if (q) search(q); });

function rowHtml(it, i, cur, editable) {
  if (it.group) return `<div class="group-title">${esc(it.group)}</div>`;
  const round = it.type === "artist" ? "round" : "";
  const fallback = { category: "note", playlist: "queue", album: "note", artist: "speaker", show: "volHigh", episode: "volHigh" }[it.type] || "note";
  const pic = it.image ? `<img class="${round}" src="${esc(it.image)}" alt="" loading="lazy">` : `<div class="ic ${round}">${svg(fallback)}</div>`;
  const dis = !it.node && !it.playable;
  return `<div class="row ${cur && it.uri === cur ? "cur" : ""} ${dis ? "dis" : ""}" data-i="${i}" role="button" tabindex="${dis ? -1 : 0}" aria-disabled="${dis}">
    ${pic}<span class="t"><div class="n">${esc(it.name)}</div>${it.subtitle ? `<div class="s">${esc(it.subtitle)}</div>` : ""}</span>
    <span class="d">${it.node ? "" : it.duration_ms ? fmt(it.duration_ms) : ""}</span>
    ${it.type === "category" ? `<span class="more">${svg("chevron")}</span>` : `<button class="more" data-act="menu" aria-label="Mehr zu ${esc(it.name)}">${svg("more")}</button>`}
  </div>`;
}

function renderBrowser() {
  const el = $("#browser");
  const p = S.page;
  const canBack = S.stack.length > 1;
  const cur = S.player && S.player.track && S.player.track.uri;
  const top = S.stack[S.stack.length - 1] || {};
  const title = (p && p.title) || top.title || "";
  const pl = p && p.playlist;
  const actions = [];
  if (p && p.context_uri) actions.push(`<button class="icon-btn" data-act="play-all" aria-label="Alles abspielen">${svg("play")}</button>`, `<button class="icon-btn" data-act="shuffle-all" aria-label="Zufällig abspielen">${svg("shuffle")}</button>`);
  if (pl && pl.editable) actions.push(`<button class="icon-btn" data-act="edit-playlist" aria-label="Playlist bearbeiten">${svg("edit")}</button>`);
  if (p && p.node === "playlists") actions.push(`<button class="icon-btn" data-act="new-playlist" aria-label="Neue Playlist">${svg("add")}</button>`);
  if (p && p.node === "root") actions.push(`<button class="icon-btn" data-act="queue" aria-label="Warteschlange">${svg("queue")}</button>`);
  let html = `<div class="head">${canBack ? `<button class="icon-btn" data-act="back" aria-label="Zurück">${svg("back")}</button>` : ""}
    <div class="h"><b>${esc(title)}</b>${p && p.total ? `<small>${p.total} Einträge</small>` : ""}</div>${actions.join("")}</div>`;
  if (S.error) html += `<div class="msg err">${esc(S.error)}</div>${S.state && S.state.web.connected ? `<button class="btn loadmore" data-act="retry">Erneut laden</button>` : ""}`;
  else if (!p && S.loading) html += `<div class="msg"><svg class="spin" viewBox="0 0 24 24"><path d="${ICON.loading}"/></svg></div>`;
  else if (p) {
    if (p.notice) html += `<div class="msg">${esc(p.notice)}</div>`;
    if (!p.items.length && !p.notice) html += `<div class="msg">${p.node === "search" ? "Keine Treffer." : "Hier ist noch nichts."}</div>`;
    html += `<div class="list">${p.items.map((it, i) => rowHtml(it, i, cur, pl && pl.editable)).join("")}</div>`;
    if (p.next_offset !== null && p.next_offset !== undefined) html += `<button class="btn loadmore" data-act="more" ${S.loading ? "disabled" : ""}>${S.loading ? "Lädt …" : "Weitere laden"}</button>`;
  }
  el.innerHTML = html;
}

async function play(uri, context, name) {
  return once("play", async () => {
    const r = await api("api/play", { method: "POST", body: { uri, context_uri: context || null } });
    toast(r.warning || `${name ? `„${name}“` : "Wiedergabe"} startet.`, Boolean(r.warning));
  });
}

$("#browser").addEventListener("click", async (ev) => {
  const act = ev.target.closest("[data-act]")?.dataset.act;
  const p = S.page;
  if (act === "back") { S.stack.pop(); const prev = S.stack.pop(); return prev.node === "search" ? search(S.query) : openNode(prev.node, false, prev.title); }
  if (act === "more") return load(p.node, p.next_offset, true);
  if (act === "retry") { const top = S.stack[S.stack.length - 1]; return top && top.node === "search" ? search(S.query) : load((top && top.node) || S.tab, 0, false); }
  if (act === "play-all") return play(p.context_uri, null, p.title);
  if (act === "shuffle-all") return once("shuf", async () => { await api("api/player/shuffle", { method: "POST", body: { on: true } }); await api("api/play", { method: "POST", body: { uri: p.context_uri } }); toast("Zufallswiedergabe startet."); });
  if (act === "new-playlist") return editPlaylist(null);
  if (act === "edit-playlist") return editPlaylist(p.playlist);
  if (act === "queue") return showQueue();
  const row = ev.target.closest("[data-i]");
  if (!row || !p) return;
  const it = p.items[Number(row.dataset.i)];
  if (!it || it.group) return;
  if (act === "menu") return itemMenu(it, Number(row.dataset.i));
  if (it.node) return openNode(it.node, false, it.name);
  if (it.playable && it.uri) return play(it.uri, it.context_uri, it.name);
});
$("#browser").addEventListener("keydown", (ev) => {
  if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches(".row[data-i]")) { ev.preventDefault(); ev.target.click(); }
});

/* ------------------------------------------------------------- sheets */
function sheet(html) {
  const s = $("#sheet");
  s.querySelector(".sheet-card").innerHTML = html;
  s.hidden = false;
  return s.querySelector(".sheet-card");
}
function closeSheet() { $("#sheet").hidden = true; }
$("#sheet").addEventListener("click", (ev) => { if (ev.target.id === "sheet" || ev.target.closest("[data-act=close]")) closeSheet(); });
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeSheet(); });

function itemMenu(it, index) {
  const pl = S.page && S.page.playlist;
  const single = ["track", "episode", "chapter"].includes(it.type);
  const items = [];
  if (it.playable) items.push(["play", "play", "Abspielen"]);
  if (it.node) items.push(["open", "chevron", "Öffnen"]);
  if (single && it.playable) items.push(["queue", "queue", "Als Nächstes einreihen"]);
  if (single && it.type === "track") items.push(["to-playlist", "add", "Zu Playlist hinzufügen …"]);
  if (it.uri && it.type !== "artist") items.push(["save", "heartO", "In Bibliothek speichern"], ["unsave", "remove", "Aus Bibliothek entfernen"]);
  if (pl && pl.editable && single) {
    items.push(["pl-remove", "remove", "Aus dieser Playlist entfernen"]);
    if (index > 0) items.push(["pl-up", "up", "Nach oben"]);
    if (index < S.page.items.length - 1) items.push(["pl-down", "down", "Nach unten"]);
  }
  const card = sheet(`<h3>${esc(it.name)}</h3><p class="hint" style="margin-top:-6px">${esc(it.subtitle || "")}</p>
    ${items.map(([a, i, l]) => `<button class="menu-item" data-m="${a}">${svg(i)}<span>${l}</span></button>`).join("")}
    <div class="btn-row"><button class="btn" data-act="close">Schließen</button></div>`);
  card.onclick = async (ev) => {
    const m = ev.target.closest("[data-m]")?.dataset.m;
    if (!m) return;
    closeSheet();
    if (m === "play") return it.node && !single ? play(it.uri, null, it.name) : play(it.uri, it.context_uri, it.name);
    if (m === "open") return openNode(it.node, false, it.name);
    if (m === "queue") return once("q", async () => { await api("api/player/queue", { method: "POST", body: { uri: it.uri } }); toast("Eingereiht."); });
    if (m === "to-playlist") return choosePlaylist([it.uri]);
    if (m === "save" || m === "unsave") return once("lib", async () => { await api("api/library", { method: "POST", body: { action: m === "save" ? "save" : "remove", uris: [it.uri] } }); toast(m === "save" ? "Gespeichert." : "Entfernt."); });
    if (m === "pl-remove") return once("plr", async () => { await api(`api/playlists/${pl.id}/items`, { method: "DELETE", body: { uris: [it.uri] } }); toast("Aus Playlist entfernt."); load(S.page.node, 0, false); });
    if (m === "pl-up" || m === "pl-down") return once("plo", async () => {
      const off = S.page.offset || 0, pos = off + index;
      await api(`api/playlists/${pl.id}/reorder`, { method: "POST", body: { range_start: pos, insert_before: m === "pl-up" ? pos - 1 : pos + 2 } });
      load(S.page.node, 0, false);
    });
  };
}

async function choosePlaylist(uris) {
  let lists = [];
  try { lists = (await api("api/browse?node=playlists&offset=0")).items; } catch (err) { return toast(err.message, true); }
  const card = sheet(`<h3>Zu Playlist hinzufügen</h3>
    <button class="menu-item" data-new="1">${svg("add")}<span>Neue Playlist …</span></button>
    ${lists.map((l, i) => `<button class="menu-item" data-pl="${i}">${svg("queue")}<span>${esc(l.name)}</span></button>`).join("")}
    <div class="btn-row"><button class="btn" data-act="close">Abbrechen</button></div>`);
  card.onclick = async (ev) => {
    if (ev.target.closest("[data-new]")) { closeSheet(); return editPlaylist(null, uris); }
    const b = ev.target.closest("[data-pl]"); if (!b) return;
    const l = lists[Number(b.dataset.pl)];
    closeSheet();
    once("pla", async () => { await api(`api/playlists/${l.id}/items`, { method: "POST", body: { uris } }); toast(`Zu „${l.name}“ hinzugefügt.`); });
  };
}

function editPlaylist(pl, addUris) {
  const card = sheet(`<h3>${pl ? "Playlist bearbeiten" : "Neue Playlist"}</h3>
    <label class="hint">Name<input class="field" id="pl-name" maxlength="100" value="${esc(pl ? pl.name : "")}"></label>
    <label class="hint">Beschreibung<input class="field" id="pl-desc" maxlength="300" value="${esc(pl ? pl.description : "")}"></label>
    <label class="hint" style="display:flex;gap:10px;align-items:center;margin-top:12px"><input type="checkbox" id="pl-public" ${pl && pl.public ? "checked" : ""}> Öffentlich</label>
    <div class="btn-row"><button class="btn primary" data-save="1">Speichern</button><button class="btn" data-act="close">Abbrechen</button></div>`);
  card.onclick = async (ev) => {
    if (!ev.target.closest("[data-save]")) return;
    const body = { name: $("#pl-name").value.trim(), description: $("#pl-desc").value, public: $("#pl-public").checked };
    if (!body.name) return toast("Bitte einen Namen eingeben.", true);
    await once("ple", async () => {
      if (pl) { await api(`api/playlists/${pl.id}`, { method: "PUT", body }); toast("Playlist gespeichert."); }
      else {
        const created = await api("api/playlists", { method: "POST", body });
        if (addUris && created.id) await api(`api/playlists/${created.id}/items`, { method: "POST", body: { uris: addUris } });
        toast(`Playlist „${body.name}“ angelegt.`);
      }
      closeSheet();
      const top = S.stack[S.stack.length - 1];
      if (top) load(top.node, 0, false);
    });
  };
}

async function showQueue() {
  let q;
  try { q = await api("api/queue"); } catch (err) { return toast(err.message, true); }
  const items = [q.currently_playing, ...(q.queue || [])].filter(Boolean);
  sheet(`<h3>Warteschlange</h3>${items.length ? `<div class="list">${items.map((it, i) => `<div class="row" style="grid-template-columns:48px 1fr">${it.image ? `<img src="${esc(it.image)}" alt="">` : `<div class="ic">${svg("note")}</div>`}<span class="t"><div class="n">${i === 0 ? "▶ " : ""}${esc(it.name)}</div><div class="s">${esc(it.subtitle || "")}</div></span></div>`).join("")}</div>` : `<p class="hint">Die Warteschlange ist leer.</p>`}
    <div class="btn-row"><button class="btn" data-act="close">Schließen</button></div>`);
}

function netHtml() {
  const n = S.state && S.state.network;
  if (!n) return "";
  const ov = Object.entries(n.overrides || {});
  const dead = (n.unreachable || []).filter((u) => !(n.overrides || {})[u.host]);
  if (!ov.length && !dead.length) return `<p class="hint">Netzwerk: alle ${n.checked} Spotify-Server erreichbar.</p>`;
  return `<h3 style="margin-top:16px">Netzwerk</h3>
    ${ov.map(([h, ip]) => `<p class="hint">${esc(h)} ist aus deinem Netz nicht erreichbar – wird über ${esc(ip)} umgeleitet.</p>`).join("")}
    ${dead.map((u) => `<p class="hint err">${esc(u.host)} (${esc(u.ips.join(", "))}) ist nicht erreichbar, keine Ausweich-IP gefunden.</p>`).join("")}`;
}

async function openSettings() {
  let devices = [], selfId = null, devErr = null;
  if (S.state && S.state.web.connected) {
    try { const r = await api("api/devices"); devices = r.devices; selfId = r.self; } catch (err) { devErr = err.message; }
  }
  const card = sheet(`<h3>Einstellungen</h3>
    <button class="menu-item" data-s="setup">${svg("edit")}<span>Einrichtung &amp; Anmeldungen</span></button>
    ${netHtml()}
    <h3 style="margin-top:16px">Home Assistant</h3>
    <p class="hint">${esc({ installed: "Integration „Spotify Flex Player“ installiert – Home Assistant einmal neu starten, dann unter Geräte & Dienste hinzufügen.", updated: "Integration aktualisiert – Home Assistant einmal neu starten.", current: "Integration „Spotify Flex Player“ ist installiert und aktuell.", disabled: "Integration ist in den App-Optionen ausgeschaltet.", unavailable: "Integration konnte nicht installiert werden (kein Zugriff auf den HA-Konfigurationsordner).", error: "Integration konnte nicht installiert werden – siehe Protokoll." }[S.state && S.state.integration] || "Status unbekannt.")}</p>
    <button class="menu-item" data-s="token">${svg("open")}<span>API-Token anzeigen (für manuelle Einrichtung)</span></button>
    <p class="hint" id="token-out" hidden></p>
    <h3 style="margin-top:16px">Spotify-Connect-Geräte</h3>
    <p class="hint">Wiedergabe von einem anderen Gerät hierher holen oder dorthin abgeben.</p>
    ${devErr ? `<p class="hint err">${esc(devErr)}</p>` : devices.map((d) => `<button class="menu-item" data-dev="${esc(d.id)}">${svg("device")}<span>${esc(d.name)}${d.id === selfId ? " (diese App)" : ""}${d.is_active ? " · aktiv" : ""}</span></button>`).join("") || `<p class="hint">Keine Geräte gemeldet.</p>`}
    <h3 style="margin-top:16px">Spotify-API direkt</h3>
    <p class="hint">Jeder Endpunkt unter <code class="inline">https://api.spotify.com/v1</code>, z. B. <code class="inline">GET /me/player/recently-played</code>.</p>
    <div style="display:flex;gap:8px"><select class="field" id="req-m" style="max-width:110px"><option>GET</option><option>POST</option><option>PUT</option><option>DELETE</option></select><input class="field" id="req-p" placeholder="/me/top/tracks"></div>
    <textarea class="field" id="req-b" placeholder='JSON-Body (optional)'></textarea>
    <div class="btn-row"><button class="btn primary" data-s="send">Senden</button><button class="btn" data-act="close">Schließen</button></div>
    <pre class="field" id="req-out" style="white-space:pre-wrap;max-height:300px;overflow:auto" hidden></pre>`);
  card.onclick = async (ev) => {
    const s = ev.target.closest("[data-s]")?.dataset.s;
    const dev = ev.target.closest("[data-dev]")?.dataset.dev;
    if (s === "setup") { closeSheet(); S.showSetup = true; renderSetup(); window.scrollTo({ top: 0, behavior: "smooth" }); }
    if (s === "token") once("tok", async () => {
      const t = await api("api/ha/token");
      const out = $("#token-out");
      out.hidden = false;
      out.innerHTML = `Host <code class="inline">127.0.0.1</code>, Port <code class="inline">${esc(t.port)}</code>, Token <code class="inline">${esc(t.token)}</code>`;
    });
    if (dev) once("tr", async () => { await api("api/devices/transfer", { method: "POST", body: { device_id: dev, play: true } }); closeSheet(); toast("Wiedergabe übertragen."); });
    if (s === "send") once("req", async () => {
      const out = $("#req-out");
      let bodyVal;
      const raw = $("#req-b").value.trim();
      if (raw) { try { bodyVal = JSON.parse(raw); } catch (_) { return toast("Der Body ist kein gültiges JSON.", true); } }
      const [path, query] = $("#req-p").value.trim().split("?");
      const params = query ? Object.fromEntries(new URLSearchParams(query)) : undefined;
      try {
        const r = await api("api/request", { method: "POST", body: { method: $("#req-m").value, path, params, body: bodyVal } });
        out.textContent = JSON.stringify(r.data, null, 2);
      } catch (err) { out.textContent = err.message; }
      out.hidden = false;
    });
  };
}

/* ------------------------------------------------------------- start */
(async function start() {
  renderTabs(); renderNow(); renderSpeakers();
  await loadState();
  connectWs();
  openNode(S.tab, true);
  setInterval(async () => {
    const needSetup = !S.state || !S.state.receiver.logged_in || !S.state.web.connected;
    if (needSetup || !document.hidden) await loadState();
    if (S.state && S.state.web.connected && !S.page && !S.loading && S.error) openNode(S.tab, true);
  }, 15000);
})();
