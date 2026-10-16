/* Spotify Flex – Einstellungsseite (nur Konfiguration, keine Wiedergabe).
   Läuft im Home-Assistant-Ingress; alle Adressen sind relativ. */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const ICON = {
  pin: "M12 17a2 2 0 0 0 2-2 2 2 0 0 0-2-2 2 2 0 0 0-2 2 2 2 0 0 0 2 2m6-9a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2h1V6a5 5 0 0 1 5-5 5 5 0 0 1 5 5v2h1m-6-5a3 3 0 0 0-3 3v2h6V6a3 3 0 0 0-3-3z",
  edit: "M20.71 7.04c.39-.39.39-1.04 0-1.41l-2.34-2.34c-.37-.39-1.02-.39-1.41 0l-1.84 1.83 3.75 3.75M3 17.25V21h3.75L17.81 9.93l-3.75-3.75L3 17.25z",
  del: "M19 4h-3.5l-1-1h-5l-1 1H5v2h14M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6v12z",
  speaker: "M12 12a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3m0 8a5 5 0 0 1-5-5 5 5 0 0 1 5-5 5 5 0 0 1 5 5 5 5 0 0 1-5 5m0-16a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2c0-1.11.9-2 2-2m5-2H7c-1.11 0-2 .89-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z",
};
const svg = (n) => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${ICON[n]}"/></svg>`;

const S = { tab: "accounts", state: null, speakers: [], groups: [], editGroup: null, busy: new Set(), openSpk: null };

/* ------------------------------------------------------------ HA-Design übernehmen */
const THEME_VARS = [
  "--primary-color", "--accent-color", "--primary-text-color", "--secondary-text-color", "--disabled-text-color",
  "--text-primary-color", "--primary-background-color", "--secondary-background-color", "--card-background-color",
  "--ha-card-background", "--divider-color", "--error-color", "--success-color", "--warning-color",
  "--ha-card-border-radius", "--ha-card-box-shadow", "--ha-card-border-color", "--ha-card-border-width",
  "--ha-font-family-body", "--paper-font-body1_-_font-family", "--input-fill-color",
];

function luminance(color) {
  const m = String(color).match(/\d+(\.\d+)?/g);
  if (!m || m.length < 3) return null;
  const [r, g, b] = m.slice(0, 3).map(Number);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
}

function syncTheme() {
  const root = document.documentElement;
  try {
    const parent = window.parent && window.parent !== window ? window.parent.document : null;
    if (!parent) return;
    const cs = getComputedStyle(parent.documentElement);
    const body = getComputedStyle(parent.body);
    let found = 0;
    for (const v of THEME_VARS) {
      const val = (cs.getPropertyValue(v) || body.getPropertyValue(v)).trim();
      if (val) { root.style.setProperty(v, val); found++; } else root.style.removeProperty(v);
    }
    if (!found) return;
    root.classList.add("ha-theme");
    const lum = luminance(getComputedStyle(root).getPropertyValue("--primary-background-color") || body.backgroundColor);
    root.classList.toggle("dark", lum !== null && lum < 0.45);
    root.style.colorScheme = lum !== null && lum < 0.45 ? "dark" : "light";
  } catch (_) { /* nicht im HA-Fenster oder kein Zugriff: Standardfarben */ }
}

function watchTheme() {
  syncTheme();
  try {
    const p = window.parent.document;
    const mo = new MutationObserver(syncTheme);
    mo.observe(p.documentElement, { attributes: true, attributeFilter: ["style", "class"] });
    mo.observe(p.head, { childList: true, subtree: true, characterData: true });
  } catch (_) { /* ignore */ }
  setInterval(syncTheme, 15000);
  matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", syncTheme);
}

/* ------------------------------------------------------------ Helfer */
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
    try { data = await res.json(); } catch (_) { /* leer */ }
    if (!res.ok) throw new Error((data && data.error) || `Fehler ${res.status}`);
    return data;
  } catch (err) {
    if (err.name === "AbortError") throw new Error("Zeitüberschreitung – bitte erneut versuchen.");
    throw err;
  } finally { clearTimeout(timer); }
}

async function once(key, fn) {
  if (S.busy.has(key)) return undefined;
  S.busy.add(key);
  try { return await fn(); } catch (err) { toast(err.message, true); return undefined; } finally { S.busy.delete(key); }
}

let toastTimer;
function toast(text, err = false) {
  const el = $("#toast");
  el.textContent = text;
  el.className = "toast" + (err ? " err" : "");
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, err ? 7000 : 3000);
}

const typing = () => {
  const a = document.activeElement;
  return a && (a.matches?.("input, select, textarea") || a.closest?.(".editor"));
};

/* ------------------------------------------------------------ Daten */
async function loadState() {
  try { S.state = await api("api/state"); } catch (_) { S.state = null; }
  renderHeader();
}

async function loadSpeakers() {
  try {
    const r = await api("api/config/speakers");
    S.speakers = r.speakers || [];
    S.groups = r.groups || [];
  } catch (err) { S.speakerError = err.message; }
}

async function refresh(force = false) {
  await Promise.all([loadState(), loadSpeakers()]);
  if (force || !typing()) render();
}

/* ------------------------------------------------------------ Kopf */
function renderHeader() {
  const st = S.state;
  $("#version").textContent = st ? `Einstellungen · Version ${st.version}` : "Einstellungen · App startet …";
  const chip = (ok, yes, no) => `<span class="chip ${ok ? "ok" : "bad"}">${ok ? yes : no}</span>`;
  $("#chips").innerHTML = st
    ? chip(st.receiver.logged_in, "Empfänger angemeldet", "Empfänger: Anmeldung nötig")
      + chip(st.web.connected, "Bibliothek verbunden", "Bibliothek: Anmeldung nötig")
      + chip(st.integration === "current" || st.integration === "updated" || st.integration === "installed", "HA-Integration", "HA-Integration fehlt")
    : `<span class="chip">verbinde …</span>`;
}

/* ------------------------------------------------------------ Ansicht */
function render() {
  document.querySelectorAll("#tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === S.tab)));
  const view = $("#view");
  if (!S.state) { view.innerHTML = `<section class="card"><h2>Spotify Flex startet …</h2><p class="desc">Die Dienste der App starten gerade. Diese Seite aktualisiert sich selbst.</p></section>`; return; }
  view.innerHTML = { accounts: viewAccounts, speakers: viewSpeakers, groups: viewGroups, system: viewSystem }[S.tab]();
}

function viewAccounts() {
  const st = S.state;
  const code = st.receiver.auth_code;
  const rec = st.receiver.logged_in
    ? `<p class="desc">Angemeldet${st.player && st.player.username ? ` als <b>${esc(st.player.username)}</b>` : ""}. In der Spotify-App heißt der Empfänger „${esc((st.player && st.player.device_name) || "Home Flex")}“.</p>
       <div class="btn-row"><button class="btn danger" data-act="receiver-logout">Abmelden</button></div>`
    : code
      ? `<p class="desc">Öffne den Link auf Handy oder PC und bestätige mit deinem Spotify-Konto. Falls nach einem Code gefragt wird:</p>
         <div class="code">${esc(code.code)}</div>
         <div class="btn-row"><a class="btn primary" href="${esc(code.url)}" target="_blank" rel="noopener">Bei Spotify bestätigen</a></div>
         <p class="hint">Gültig bis ${esc(new Date(code.expires_at).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }))} Uhr, danach erscheint automatisch ein neuer Code.</p>`
      : st.receiver.running ? `<p class="desc">Warte auf den Anmeldecode von Spotify …</p>` : `<p class="desc err">Der Empfänger läuft nicht. Bitte das Protokoll der App prüfen.</p>`;
  let web;
  if (st.web.connected) {
    web = `<p class="desc">Bibliothek, Playlists und Suche sind verbunden.</p><div class="btn-row"><button class="btn danger" data-act="web-logout">Trennen</button></div>`;
  } else if (!st.web.configured) {
    web = `<p class="desc">Trage unter <b>Einstellungen → Apps → Spotify Flex → Konfiguration</b> die <b>Client-ID</b> deiner Spotify-Entwickler-App ein und starte die App neu. Ein Client-Secret ist nicht nötig.</p>`;
  } else {
    web = `<p class="desc">1. Im <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener">Spotify-Entwickler-Dashboard</a> bei deiner App unter <i>Redirect URIs</i> diese Adresse eintragen: <code>${esc(st.web.redirect_uri)}</code></p>
      <p class="desc">2. Anmelden. Danach landest du auf einer Seite, die nicht lädt – das ist richtig.</p>
      <div class="btn-row"><button class="btn primary" data-act="web-login">Mit Spotify anmelden</button></div>
      <p class="desc" style="margin-top:12px">3. Die komplette Adresse dieser Seite hier einfügen:</p>
      <input class="field" id="web-paste" placeholder="http://127.0.0.1:8765/callback?code=…">
      <div class="btn-row"><button class="btn primary" data-act="web-finish">Übernehmen</button></div>`;
  }
  return `<section class="card"><h2>Spotify-Empfänger <span class="state ${st.receiver.logged_in ? "ok-text" : "err"}">${st.receiver.logged_in ? "angemeldet" : "nicht angemeldet"}</span></h2>${rec}</section>
    <section class="card"><h2>Spotify-Bibliothek <span class="state ${st.web.connected ? "ok-text" : "err"}">${st.web.connected ? "verbunden" : "nicht verbunden"}</span></h2>${web}</section>`;
}

function volField(s, key, label) {
  const v = s[key];
  const on = v !== null && v !== undefined;
  return `<div class="lbl"><span>${label}</span>
    <div class="vol">
      <button class="switch" role="switch" aria-checked="${on}" data-act="vol-toggle" data-key="${key}" aria-label="${label} festlegen"></button>
      ${on ? `<input type="range" min="0" max="100" value="${v}" data-key="${key}" aria-label="${label}"><span class="v">${v} %</span>` : `<span class="v" style="text-align:left;color:var(--secondary-text-color)">aus</span>`}
    </div></div>`;
}

function viewSpeakers() {
  if (!S.speakers.length) return `<section class="card"><h2>Lautsprecher</h2><p class="desc">${esc(S.speakerError || "Noch keine AirPlay-Lautsprecher gefunden. Sie müssen im selben Netz und eingeschaltet sein – die Suche läuft automatisch.")}</p></section>`;
  const rows = S.speakers.map((s) => `
    <div class="spk ${s.hidden ? "hidden" : ""}" data-id="${esc(s.id)}">
      <div class="spk-head">
        <span class="icon-btn" aria-hidden="true">${svg("speaker")}</span>
        <div class="grow"><div class="name">${esc(s.name)}</div>
          <div class="meta">${esc(s.type || "AirPlay")}${s.alias ? ` · Gerätename „${esc(s.device_name)}“` : ""}${s.hidden ? " · ausgeblendet" : ""}${s.needs_pin ? " · Kopplung nötig" : ""}</div></div>
        ${s.needs_pin ? `<button class="btn" data-act="pair">${svg("pin")} Koppeln</button>` : ""}
        <button class="icon-btn" data-act="spk-open" aria-label="${esc(s.name)} bearbeiten" aria-expanded="${S.openSpk === s.id}">${svg("edit")}</button>
      </div>
      ${S.openSpk === s.id ? `<div class="spk-form">
        <label class="lbl"><span>Anzeigename</span><input class="field" data-key="alias" value="${esc(s.alias || "")}" placeholder="${esc(s.device_name)}" maxlength="60"></label>
        ${volField(s, "start_volume", "Lautstärke beim Einschalten")}
        ${volField(s, "max_volume", "Maximale Lautstärke")}
        <label class="lbl inline"><button class="switch" role="switch" aria-checked="${!!s.hidden}" data-act="hide"></button><span>Ausblenden (nicht im Player und nicht in Home Assistant)</span></label>
      </div>` : ""}
    </div>`).join("");
  return `<section class="card"><h2>Lautsprecher</h2>
    <p class="desc">Namen, Start- und Höchstlautstärke festlegen oder Lautsprecher ausblenden. Änderungen werden sofort gespeichert.</p>${rows}</section>`;
}

function viewGroups() {
  const name = (id) => (S.speakers.find((s) => s.id === id) || {}).name;
  const editor = (g) => `<div class="editor" data-gid="${esc(g ? g.id : "")}">
      <label class="lbl"><span>Name der Gruppe</span><input class="field" id="g-name" value="${esc(g ? g.name : "")}" placeholder="z. B. Erdgeschoss" maxlength="60"></label>
      <div class="checks">${S.speakers.map((s) => `<label><input type="checkbox" value="${esc(s.id)}" ${g && g.speakers.includes(s.id) ? "checked" : ""}>${esc(s.name)}</label>`).join("")}</div>
      <div class="btn-row"><button class="btn primary" data-act="g-save">Speichern</button><button class="btn" data-act="g-cancel">Abbrechen</button></div>
    </div>`;
  const rows = S.groups.map((g) => `
    <div class="grp" data-gid="${esc(g.id)}">
      <div class="grow">
        <div class="name">${esc(g.name)}</div>
        <div class="members">${g.speakers.map((id) => name(id) ? `<span class="member">${esc(name(id))}</span>` : `<span class="member missing">nicht gefunden</span>`).join("")}</div>
        ${S.editGroup === g.id ? editor(g) : ""}
      </div>
      <button class="icon-btn" data-act="g-edit" aria-label="${esc(g.name)} bearbeiten">${svg("edit")}</button>
      <button class="icon-btn" data-act="g-del" aria-label="${esc(g.name)} löschen">${svg("del")}</button>
    </div>`).join("");
  return `<section class="card"><h2>Lautsprecher-Gruppen</h2>
    <p class="desc">Eine Gruppe schaltet genau ihre Lautsprecher ein und alle anderen aus. Im Player und in Home Assistant erscheinen Gruppen als Quelle und in der Gruppenauswahl.</p>
    ${rows || `<p class="hint">Noch keine Gruppen angelegt.</p>`}
    ${S.editGroup === "new" ? editor(null) : `<div class="btn-row"><button class="btn primary" data-act="g-new" ${S.speakers.length ? "" : "disabled"}>Neue Gruppe</button></div>`}
  </section>`;
}

function viewSystem() {
  const st = S.state;
  const integ = { installed: "installiert – Home Assistant einmal neu starten", updated: "aktualisiert – Home Assistant einmal neu starten", current: "installiert und aktuell", disabled: "in den App-Optionen ausgeschaltet", unavailable: "konnte nicht installiert werden (kein Zugriff auf den HA-Ordner)", error: "Fehler – siehe Protokoll" }[st.integration] || "unbekannt";
  const lat = st.player && st.player.track && st.player.track.latency_ms;
  const net = st.network;
  let netHtml = `<p class="hint">Noch kein Bericht.</p>`;
  if (net) {
    const when = new Date(net.checked_at * 1000).toLocaleString("de-DE", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
    netHtml = (net.unreachable || []).length
      ? `<p class="desc">Geprüft am ${esc(when)}: ${net.unreachable.length} Spotify-Server aus deinem Netz nicht erreichbar – werden automatisch umgeleitet.</p>
         <dl class="kv">${net.unreachable.map((u) => `<dt>${esc(u.host)}</dt><dd>${esc(u.ips.join(", "))} → ${esc(net.overrides[u.host] || "keine Ausweich-Adresse")}</dd>`).join("")}</dl>`
      : `<p class="desc ok-text">Geprüft am ${esc(when)}: alle ${esc(net.checked)} Spotify-Server erreichbar.</p>`;
  }
  return `<section class="card"><h2>Home Assistant</h2>
      <dl class="kv"><dt>Integration</dt><dd>Spotify Flex Player – ${esc(integ)}</dd>
        <dt>Audio-Verzögerung</dt><dd>${lat ? `${(lat / 1000).toFixed(2).replace(".", ",")} s (gemessen, für den Liedtext)` : "wird beim Abspielen gemessen"}</dd></dl>
      <div class="btn-row"><button class="btn" data-act="token">API-Token anzeigen</button></div>
      <p class="hint" id="token-out" hidden></p>
    </section>
    <section class="card"><h2>App-Optionen</h2>
      <p class="desc">Gerätename, Klangqualität, Lautstärke-Normalisierung, Zeroconf und Client-ID stellst du unter <b>Einstellungen → Apps → Spotify Flex → Konfiguration</b> ein. Danach startet die App neu.</p>
    </section>
    <section class="card"><h2>Netzwerk</h2>${netHtml}</section>`;
}

/* ------------------------------------------------------------ Aktionen */
async function saveSpeaker(id, values) {
  const r = await api(`api/config/speakers/${encodeURIComponent(id)}`, { method: "PUT", body: values });
  S.speakers = r.all || S.speakers;
  S.groups = r.groups || S.groups;
}

document.addEventListener("click", async (ev) => {
  const tab = ev.target.closest("#tabs button");
  if (tab) { S.tab = tab.dataset.tab; S.editGroup = null; try { localStorage.setItem("sf-tab", S.tab); } catch (_) { /* privat */ } render(); return; }
  const el = ev.target.closest("[data-act]");
  if (!el) return;
  const act = el.dataset.act;
  const spk = el.closest(".spk");
  const sid = spk && spk.dataset.id;
  const s = sid && S.speakers.find((x) => x.id === sid);
  switch (act) {
    case "web-login": return once("login", async () => { const r = await api("api/web/authorize", { method: "POST" }); window.open(r.url, "_blank", "noopener"); });
    case "web-finish": return once("finish", async () => {
      const r = await api("api/web/finish", { method: "POST", body: { url: $("#web-paste").value } });
      toast(`Bibliothek verbunden${r.name ? ` (${r.name})` : ""}.`); await refresh(true);
    });
    case "web-logout": if (!confirm("Bibliothek wirklich trennen?")) return undefined;
      return once("wlo", async () => { await api("api/web/logout", { method: "POST" }); await refresh(true); });
    case "receiver-logout": if (!confirm("Empfänger wirklich von Spotify abmelden?")) return undefined;
      return once("rlo", async () => { await api("api/receiver/logout", { method: "POST" }); setTimeout(() => refresh(true), 3000); });
    case "spk-open": S.openSpk = S.openSpk === sid ? null : sid; return render();
    case "hide": return once("hide" + sid, async () => { await saveSpeaker(sid, { hidden: !s.hidden }); render(); toast(s.hidden ? "Lautsprecher wird wieder angezeigt." : "Lautsprecher ausgeblendet."); });
    case "vol-toggle": {
      const key = el.dataset.key;
      const on = s[key] !== null && s[key] !== undefined;
      return once("vt" + sid, async () => { await saveSpeaker(sid, { [key]: on ? null : (key === "max_volume" ? 80 : 40) }); render(); });
    }
    case "pair": return once("pair" + sid, async () => {
      const first = await api(`api/config/speakers/${encodeURIComponent(sid)}/pair`, { method: "POST", body: {} });
      if (first && first.paired) { toast("Bereits gekoppelt."); await refresh(true); return; }
      const pin = prompt(`${s.name} zeigt jetzt eine PIN an (z. B. auf dem Fernseher). Bitte eingeben:`);
      if (!pin) return;
      await api(`api/config/speakers/${encodeURIComponent(sid)}/pair`, { method: "POST", body: { pin } });
      toast(`${s.name} ist gekoppelt.`); await refresh(true);
    });
    case "g-new": S.editGroup = "new"; render(); $("#g-name")?.focus(); return undefined;
    case "g-edit": { const gid = el.closest(".grp").dataset.gid; S.editGroup = S.editGroup === gid ? null : gid; render(); return undefined; }
    case "g-cancel": S.editGroup = null; return render();
    case "g-save": return once("gsave", async () => {
      const box = el.closest(".editor");
      const name = $("#g-name", box).value.trim();
      const speakers = [...box.querySelectorAll("input[type=checkbox]:checked")].map((c) => c.value);
      const gid = box.dataset.gid;
      const r = gid
        ? await api(`api/groups/${encodeURIComponent(gid)}`, { method: "PUT", body: { name, speakers } })
        : await api("api/groups", { method: "POST", body: { name, speakers } });
      S.groups = r.groups || S.groups; S.editGroup = null; render();
      toast(`Gruppe „${name}“ gespeichert.`);
    });
    case "g-del": {
      const g = S.groups.find((x) => x.id === el.closest(".grp").dataset.gid);
      if (!g || !confirm(`Gruppe „${g.name}“ löschen?`)) return undefined;
      return once("gdel", async () => { const r = await api(`api/groups/${encodeURIComponent(g.id)}`, { method: "DELETE" }); S.groups = r.groups || []; render(); });
    }
    case "token": return once("tok", async () => {
      const t = await api("api/ha/token");
      const out = $("#token-out");
      out.hidden = false;
      out.innerHTML = `Für die manuelle Einrichtung: Host <code>127.0.0.1</code>, Port <code>${esc(t.port)}</code>, Token <code>${esc(t.token)}</code>`;
    });
    default: return undefined;
  }
});

document.addEventListener("input", (ev) => {
  const t = ev.target;
  if (t.matches(".spk input[type=range]")) t.nextElementSibling.textContent = `${t.value} %`;
});

document.addEventListener("change", (ev) => {
  const t = ev.target;
  const spk = t.closest(".spk");
  if (!spk || !t.dataset.key) return;
  const key = t.dataset.key;
  const value = key === "alias" ? t.value : Number(t.value);
  once("save" + spk.dataset.id + key, async () => {
    await saveSpeaker(spk.dataset.id, { [key]: value });
    if (key === "alias") { render(); toast("Name gespeichert."); }
  });
});

/* ------------------------------------------------------------ Start */
try { const saved = localStorage.getItem("sf-tab"); if (saved) S.tab = saved; } catch (_) { /* privat */ }
watchTheme();
render();
refresh(true);
setInterval(() => refresh(false), 15000);
