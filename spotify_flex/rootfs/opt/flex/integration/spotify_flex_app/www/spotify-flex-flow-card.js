/*
 * Spotify Flex Flow – Player-Kachel im Aufbau von HOMEii Flow, für die Spotify-Flex-App.
 * Helles Neumorph ohne Logo/Farbverlauf, Liedtext synchron zum AirPlay-Ton, Mediathek,
 * Suche, Warteschlange, Lieblingssongs, Sleep-Timer, Equalizer und Lautsprecher/Gruppen.
 */
const CARD_VERSION = "1.7.0";
const DOMAIN = "spotify_flex_app";

const P = {
  play: "M8 5.14v14l11-7-11-7z",
  pause: "M14 19h4V5h-4M6 19h4V5H6v14z",
  next: "M16 18h2V6h-2M6 18l8.5-6L6 6v12z",
  prev: "M6 18V6h2v12H6m3.5-6L18 6v12l-8.5-6z",
  shuffle: "M14.83 13.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13M14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41z",
  repeat: "M17 17H7v-3l-4 4 4 4v-3h12v-6h-2M7 7h10v3l4-4-4-4v3H5v6h2V7z",
  repeatOne: "M13 15V9h-1l-2 1v1h1.5v4M17 17H7v-3l-4 4 4 4v-3h12v-6h-2M7 7h10v3l4-4-4-4v3H5v6h2V7z",
  heart: "M12 21.35l-1.45-1.32C5.4 15.36 2 12.27 2 8.5 2 5.41 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.08C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.41 22 8.5c0 3.77-3.4 6.86-8.55 11.53L12 21.35z",
  heartO: "M12.1 18.55l-.1.1-.11-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04 1 3.57 2.36h1.86C13.46 6 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05M16.5 3c-1.74 0-3.41.81-4.5 2.08C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.41 2 8.5c0 3.77 3.4 6.86 8.55 11.53L12 21.35l1.45-1.32C18.6 15.36 22 12.27 22 8.5 22 5.41 19.58 3 16.5 3z",
  queue: "M3 10h11v2H3v-2m0-4h11v2H3V6m0 8h7v2H3v-2m13-1v8l6-4-6-4z",
  timer: "M12 20a7 7 0 0 1-7-7 7 7 0 0 1 7-7 7 7 0 0 1 7 7 7 7 0 0 1-7 7m7.03-12.62 1.42-1.42c-.45-.51-.9-.97-1.41-1.41L17.62 6c-1.55-1.26-3.5-2-5.62-2a9 9 0 0 0-9 9 9 9 0 0 0 9 9c5 0 9-4.03 9-9 0-2.12-.74-4.07-1.97-5.62M11 14h2V8h-2m4-7H9v2h6V1z",
  history: "M13.5 8H12v5l4.28 2.54.72-1.21-3.5-2.08V8M13 3a9 9 0 0 0-9 9H1l3.96 4.03L9 12H6a7 7 0 0 1 7-7 7 7 0 0 1 7 7 7 7 0 0 1-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.896 8.896 0 0 0 13 21a9 9 0 0 0 9-9 9 9 0 0 0-9-9",
  speaker: "M12 12a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3m0 8a5 5 0 0 1-5-5 5 5 0 0 1 5-5 5 5 0 0 1 5 5 5 5 0 0 1-5 5m0-16a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2c0-1.11.9-2 2-2m5-2H7c-1.11 0-2 .89-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z",
  vol: "M14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.84-5 6.7v2.07c4-.91 7-4.49 7-8.77 0-4.28-3-7.86-7-8.77M16.5 12c0-1.77-1-3.29-2.5-4.03V16c1.5-.71 2.5-2.24 2.5-4M3 9v6h4l5 5V4L7 9H3z",
  volOff: "M12 4 9.91 6.09 12 8.18M4.27 3 3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.26c-.67.51-1.42.93-2.25 1.17v2.07c1.38-.32 2.63-.95 3.68-1.81L19.73 21 21 19.73l-9-9M19 12c0 .94-.2 1.82-.54 2.64l1.51 1.51A8.916 8.916 0 0 0 21 12c0-4.28-3-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71m-2.5 0c0-1.77-1-3.29-2.5-4.03v2.21l2.45 2.45c.05-.2.05-.42.05-.63z",
  plus: "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
  minus: "M19 13H5v-2h14v2z",
  close: "M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z",
  back: "M20 11v2H8l5.5 5.5-1.42 1.42L4.16 12l7.92-7.92L13.5 5.5 8 11h12z",
  search: "M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.516 6.516 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5z",
  dots: "M12 16a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2 2 2 0 0 1 2-2m0-6a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2 2 2 0 0 1 2-2m0-6a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2 2 2 0 0 1 2-2z",
  grid: "M3 11h8V3H3m0 18h8v-8H3m10 8h8v-8h-8m0-10v8h8V3",
  list: "M3 4h18v2H3V4m0 7h18v2H3v-2m0 7h18v2H3v-2z",
  note: "M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z",
  album: "M12 11a1 1 0 0 0-1 1 1 1 0 0 0 1 1 1 1 0 0 0 1-1 1 1 0 0 0-1-1m0 5.5c-2.5 0-4.5-2-4.5-4.5S9.5 7.5 12 7.5s4.5 2 4.5 4.5-2 4.5-4.5 4.5M12 2A10 10 0 0 0 2 12a10 10 0 0 0 10 10 10 10 0 0 0 10-10A10 10 0 0 0 12 2z",
  artist: "M11 14c1 0 2.05.16 3.2.44-.81.87-1.2 1.89-1.2 3.06 0 .89.25 1.73.78 2.5H3v-2c0-.89.5-1.73 1.44-2.5.96-.78 2.23-1.39 3.81-1.85S10.81 14 11 14m0-2c-1.08 0-2-.39-2.8-1.17C7.41 10.05 7 9.11 7 8c0-1.08.41-2 1.2-2.8C9 4.41 9.92 4 11 4c1.11 0 2.05.41 2.83 1.2.78.8 1.17 1.72 1.17 2.8 0 1.11-.39 2.05-1.17 2.83-.78.78-1.72 1.17-2.83 1.17m7.5 2H22v2h-2v5.5a2.5 2.5 0 0 1-2.5 2.5 2.5 2.5 0 0 1-2.5-2.5 2.5 2.5 0 0 1 2.5-2.5c.36 0 .69.07 1 .21V14z",
  podcast: "M17 18.25V21.5H7v-3.25c0-1.25 2.25-2.25 5-2.25s5 1 5 2.25M12 5.5a6.5 6.5 0 0 1 6.5 6.5c0 1.25-.35 2.42-.96 3.41L16 14.5c.32-.75.5-1.6.5-2.5a4.5 4.5 0 0 0-4.5-4.5A4.5 4.5 0 0 0 7.5 12c0 .9.18 1.75.5 2.5l-1.54.91A6.5 6.5 0 0 1 5.5 12 6.5 6.5 0 0 1 12 5.5m0 3.5a3 3 0 0 1 3 3 3 3 0 0 1-3 3 3 3 0 0 1-3-3 3 3 0 0 1 3-3m0-7A10 10 0 0 1 22 12c0 2.25-.75 4.33-2 6l-1.5-1c.94-1.42 1.5-3.15 1.5-5a8 8 0 0 0-8-8 8 8 0 0 0-8 8c0 1.85.56 3.58 1.5 5L4 18c-1.25-1.67-2-3.75-2-6A10 10 0 0 1 12 2z",
  playlist: "M15 6H3v2h12V6m0 4H3v2h12v-2M3 16h8v-2H3v2M17 6v8.18c-.31-.11-.65-.18-1-.18a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V8h3V6h-5z",
  power: "M16.56 5.44l-1.45 1.45A5.969 5.969 0 0 1 18 12a6 6 0 0 1-6 6 6 6 0 0 1-6-6c0-2.17 1.16-4.06 2.88-5.12L7.44 5.44A7.961 7.961 0 0 0 4 12a8 8 0 0 0 8 8 8 8 0 0 0 8-8c0-2.72-1.36-5.12-3.44-6.56M13 3h-2v10h2",
  queueAdd: "M3 16h7v-2H3m11 0v-4h-2v4H8v2h4v4h2v-4h4v-2m-4-8H3v2h11m0-6H3v2h11V4z",
};
// eigene Strich-Icons aus Fabs HOMEii-Anpassung (Liedtext / Musik auswählen)
const STROKE = {
  lyrics: '<path d="M6 3h9l3 3v15H6zM15 3v4h3M9 11h6M9 15h6M9 19h4"/>',
  browse: '<path d="M3 5h13M3 10h13M3 15h9M20 7v10a2.5 2.5 0 1 1-2-2.45V9l4-1"/>',
  eq: '<path d="M6 3v5M6 12v9M12 3v11M12 18v3M18 3v2M18 9v12"/><circle cx="6" cy="10" r="2"/><circle cx="12" cy="16" r="2"/><circle cx="18" cy="7" r="2"/>',
};
const svg = (name) => STROKE[name]
  ? `<svg viewBox="0 0 24 24" aria-hidden="true" class="st">${STROKE[name]}</svg>`
  : `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${P[name] || P.note}"/></svg>`;
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const fmt = (s) => {
  if (!Number.isFinite(s) || s < 0) return "0:00";
  s = Math.floor(s);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
};
const lsGet = (k, d) => { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (_) { return d; } };
/* prägende Farbe eines Covers: Farbton mit dem meisten "Gewicht" (Sättigung × Fläche), sonst Grau */
function coverColor(img) {
  const n = 40, c = document.createElement("canvas");
  c.width = n; c.height = n;
  const ctx = c.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, n, n);
  const d = ctx.getImageData(0, 0, n, n).data;   // wirft bei CORS-gesperrten Bildern
  const bins = new Array(24).fill(0).map(() => ({ w: 0, x: 0, y: 0, s: 0 }));
  let total = 0;
  for (let i = 0; i < d.length; i += 4) {
    const r = d[i] / 255, g = d[i + 1] / 255, b = d[i + 2] / 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, ch = mx - mn;
    if (l < 0.08 || l > 0.95) continue;                       // fast schwarz/weiß zählt nicht
    const sat = ch === 0 ? 0 : ch / (1 - Math.abs(2 * l - 1));
    let h = 0;
    if (ch) h = mx === r ? ((g - b) / ch) % 6 : mx === g ? (b - r) / ch + 2 : (r - g) / ch + 4;
    h = (h * 60 + 360) % 360;
    const w = sat * (1 - Math.abs(l - 0.5));                   // kräftige, mittelhelle Farben zählen mehr
    total += 1;
    if (sat < 0.1) continue;
    const bin = bins[Math.floor(h / 15) % 24];
    bin.w += w; bin.x += Math.cos(h * Math.PI / 180) * w; bin.y += Math.sin(h * Math.PI / 180) * w; bin.s += sat * w;
  }
  const best = bins.reduce((a, b) => (b.w > a.w ? b : a));
  if (!total || best.w < total * 0.008) return [215, 0];        // kaum Farbe im Bild -> neutrales Grau
  const hue = Math.round((Math.atan2(best.y, best.x) * 180 / Math.PI + 360) % 360);
  return [hue, best.s / best.w];
}

try {  // Farbwechsel weich überblenden
  for (const name of ["--sf-bg", "--sf-hi", "--sf-lo", "--sf-lo2"]) CSS.registerProperty({ name, syntax: "<color>", inherits: true, initialValue: "#ffffff" });
} catch (_) { /* schon registriert oder nicht unterstützt */ }

const lsSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) { /* privat */ } };

const TABS = [
  { id: "search", label: "Suche", icon: "search" },
  { id: "playlists", label: "Playlists", icon: "playlist", node: "playlists" },
  { id: "liked", label: "Lieblingssongs", icon: "heart", node: "liked" },
  { id: "albums", label: "Alben", icon: "album", node: "albums" },
  { id: "artists", label: "Künstler", icon: "artist", node: "artists" },
  { id: "recent", label: "Zuletzt gehört", icon: "history", node: "recent" },
  { id: "shows", label: "Podcasts", icon: "podcast", node: "shows" },
];
const NODE = "flex:node:";

/* Spotify-Link oder -URI (z. B. aus „Teilen → Link kopieren“) → URI.
   Damit lassen sich auch Spotify-eigene Playlists („This Is …“, Mixe) abspielen,
   die Spotify seit Ende 2024 über die Web-API weder in der Suche noch beim Öffnen herausgibt. */
export function spotifyLink(text) {
  const t = String(text || "").trim();
  let m = t.match(/open\.spotify\.com\/(?:intl-[a-z-]+\/)?(playlist|album|track|artist|show|episode)\/([A-Za-z0-9]{10,40})/);
  if (!m) m = t.match(/^spotify:(playlist|album|track|artist|show|episode):([A-Za-z0-9]{10,40})$/);
  return m ? { type: m[1], uri: `spotify:${m[1]}:${m[2]}` } : null;
}

const TS = /\[(\d+):(\d+(?:[.,]\d+)?)\]/g;
const WTS = /<(\d+):(\d+(?:[.,]\d+)?)>/g;
const toMs = (m, sec) => (Number(m) * 60 + Number(String(sec).replace(",", "."))) * 1000;
// grobe Silbenzahl (dt./engl.): Vokalgruppen zählen
const syllables = (w) => Math.max(1, (String(w).toLowerCase().match(/[aeiouyäöü]+/g) || []).length);

/* LRC → Zeilen mit Wort-Zeitpunkten. Erweitertes LRC (<mm:ss.xx> je Wort) wird genutzt,
   sonst werden die Wörter nach Silben über die gesungene Dauer der Zeile verteilt. */
export function parseLrc(raw) {
  const lines = [];
  String(raw || "").split(/\r?\n/).forEach((line) => {
    const stamps = [...line.matchAll(TS)];
    if (!stamps.length) return;
    const body = line.replace(TS, "");
    const marks = [...body.matchAll(WTS)];
    let words = null;
    if (marks.length) {
      words = [];
      const parts = body.split(WTS);
      // parts: [vorher, m, s, text, m, s, text, ...]
      for (let i = 1; i + 2 < parts.length + 1; i += 3) {
        const text = (parts[i + 2] || "").trim();
        if (text) text.split(/\s+/).forEach((w, k) => words.push({ w, t: toMs(parts[i], parts[i + 1]) + k * 120 }));
      }
    }
    const text = body.replace(WTS, "").replace(/\s+/g, " ").trim();
    stamps.forEach((m) => lines.push({ t: toMs(m[1], m[2]), text, words: words ? words.map((x) => ({ ...x })) : null }));
  });
  const out = lines.filter((l) => l.text).sort((a, b) => a.t - b.t);
  out.forEach((l, i) => {
    const next = out[i + 1] ? out[i + 1].t : l.t + 6000;
    // Satzzeichen ohne Buchstaben (z. B. „–“) hängen am vorigen Wort, damit der Punkt dort nicht hüpft
    const tokens = [];
    l.text.split(" ").filter(Boolean).forEach((w) => {
      if (tokens.length && !/[\p{L}\p{N}]/u.test(w)) tokens[tokens.length - 1] += ` ${w}`; else tokens.push(w);
    });
    if (l.words && l.words.length === tokens.length) { l.end = Math.min(next, l.words[l.words.length - 1].t + 900); return; }
    const syl = tokens.map(syllables);
    const total = syl.reduce((a, b) => a + b, 0);
    // gesungene Dauer: ca. 0,27 s je Silbe, höchstens bis kurz vor die nächste Zeile
    const sung = Math.max(600, Math.min((next - l.t) * 0.92, total * 270 + 250));
    let acc = 0;
    l.words = tokens.map((w, k) => { const t = l.t + (acc / total) * sung; acc += syl[k]; return { w, t }; });
    l.end = l.t + sung;
  });
  return out;
}

class SpotifyFlexFlowCard extends HTMLElement {
  static getStubConfig() { return { entity: "media_player.spotify_flex_player" }; }
  static getConfigElement() { return null; }

  setConfig(config) {
    this._config = {
      entity: "media_player.spotify_flex_player",
      height: 600,
      lyrics_offset: 0, // Sekunden Feinkorrektur – die Audio-Verzögerung misst die App selbst
      cover_flow: true,
      ...config,
    };
    if (!/^media_player\./.test(this._config.entity)) throw new Error("entity muss ein media_player sein");
    this._ls = `sfflow:${this._config.entity}:`;
    this._s = {
      sheet: null, eq: null, eqDrag: null, lyricsOn: lsGet(this._ls + "lyrics", true), offset: lsGet(this._ls + "fine", null),
      lib: { tab: "playlists", stack: [], view: lsGet(this._ls + "view", "grid"), query: "" },
      liked: null, likedUri: null, lyrics: null, lyricsKey: null, prevArt: null, lastArt: null,
      nextArt: null, queueKey: null, busy: new Set(),
    };
    if (this.shadowRoot) this._build();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (!this.shadowRoot) { this.attachShadow({ mode: "open" }); this._build(); }
    if (first) {
      this._observe();
      // Equalizer-Status für den Button (grün = an); ältere Integration ohne Dienst: still ignorieren
      if (hass.services?.[DOMAIN]?.equalizer) this._resp("equalizer").then((r) => { if (!this._s.eq) this._s.eq = r; this._eqMark(); }).catch(() => {});
    }
    this._update();
  }

  getCardSize() { return Math.ceil((this._config?.height || 600) / 50); }
  getGridOptions() { return { columns: "full", rows: Math.ceil((this._config?.height || 600) / 56), min_rows: 8 }; }

  connectedCallback() {
    if (!this._tick) this._tick = setInterval(() => this._frame(), 250);
    if (this._s?.lyrics?.lines?.length) this._ballLoop();
    this._observe();
  }

  disconnectedCallback() {
    clearInterval(this._tick); this._tick = null;
    if (this._raf) { cancelAnimationFrame(this._raf); this._raf = null; }
    this._ro?.disconnect(); this._ro = null;
  }

  _observe() {
    if (this._ro || !this.shadowRoot) return;
    this._ro = new ResizeObserver(() => this._layout());
    this._ro.observe(this);
  }

  /* ------------------------------------------------------------ helpers */
  get _st() { return this._hass?.states?.[this._config.entity]; }
  get _attrs() { return this._st?.attributes || {}; }
  _$(sel) { return this.shadowRoot.querySelector(sel); }

  _speakers() {
    const hass = this._hass;
    const listed = this._attrs.speaker_entities;
    if (Array.isArray(listed) && listed.length) {
      return listed.map((id) => hass.states[id]).filter(Boolean)
        .sort((a, b) => this._speakerName(a).localeCompare(this._speakerName(b), "de"));
    }
    const ents = hass?.entities || {};
    return Object.keys(hass?.states || {})
      .filter((id) => id.startsWith("media_player.") && id !== this._config.entity
        && (ents[id]?.platform === DOMAIN || (!ents[id] && /_spotify_flex$/.test(id))))
      .map((id) => hass.states[id])
      .sort((a, b) => String(a.attributes.friendly_name).localeCompare(String(b.attributes.friendly_name), "de"));
  }

  _groupEntity() {
    const hass = this._hass;
    if (this._config.group_entity) return hass.states[this._config.group_entity];
    if (this._attrs.group_entity && hass.states[this._attrs.group_entity]) return hass.states[this._attrs.group_entity];
    const ents = hass?.entities || {};
    const id = Object.keys(hass?.states || {}).find((e) => e.startsWith("select.")
      && (ents[e]?.platform === DOMAIN || (!ents[e] && /^select\.spotify_flex_(lautsprecher_gruppe|speaker_group)$/.test(e))));
    return id ? hass.states[id] : null;
  }

  _speakerName(st) {
    return String(st.attributes.friendly_name || st.entity_id).replace(/\s*Spotify Flex$/i, "");
  }

  /* Uhrabweichung Browser ↔ Home Assistant: aus live beobachteten Positions-Updates
     (Zustellung dauert nur Millisekunden) – sonst wäre der Liedtext je nach Gerät versetzt. */
  _trackSkew() {
    const upd = this._attrs.media_position_updated_at;
    if (!upd || upd === this._s.lastUpd) return;
    const first = this._s.lastUpd === undefined;
    this._s.lastUpd = upd;
    if (first) return; // Wert beim Laden kann alt sein
    if (!(Number(this._attrs.media_position) > 0)) return; // Startzeit in der Zukunft (Titelwechsel)
    const sample = Date.now() - new Date(upd).getTime();
    if (!Number.isFinite(sample)) return;
    const arr = (this._s.skews = [...(this._s.skews || []), sample].slice(-12));
    this._s.skew = Math.min(...arr);
  }

  _position() {
    const a = this._attrs;
    let pos = Number(a.media_position || 0);
    if (this._st?.state === "playing" && a.media_position_updated_at) {
      const el = (Date.now() - (this._s.skew || 0) - new Date(a.media_position_updated_at).getTime()) / 1000;
      if (el > 0 && Number.isFinite(el)) pos += el;
    }
    const dur = Number(a.media_duration || 0);
    return dur ? Math.min(pos, dur) : pos;
  }

  _offset() {
    if (this._s.offset !== null && this._s.offset !== undefined) return Number(this._s.offset);
    return Number(this._config.lyrics_offset) || 0;
  }

  async _svc(domain, service, data = {}) {
    try {
      await this._hass.callService(domain, service, data);
    } catch (err) {
      this._toast(err?.message || String(err), true);
      throw err;
    }
  }

  async _resp(service, data = {}) {
    const r = await this._hass.callWS({ type: "call_service", domain: DOMAIN, service, service_data: data, return_response: true });
    return r?.response || {};
  }

  async _once(key, fn) {
    if (this._s.busy.has(key)) return;
    this._s.busy.add(key);
    try { await fn(); } catch (err) { if (err && !err._shown) this._toast(err.message || String(err), true); }
    finally { this._s.busy.delete(key); }
  }

  _player(service, data = {}) { return this._svc("media_player", service, { entity_id: this._config.entity, ...data }); }

  _toast(text, err = false) {
    const t = this._$(".toast");
    if (!t) return;
    t.textContent = text;
    t.classList.toggle("err", !!err);
    t.classList.add("show");
    clearTimeout(this._toastT);
    this._toastT = setTimeout(() => t.classList.remove("show"), err ? 5200 : 2600);
  }

  /* ------------------------------------------------------------- build */
  _build() {
    const h = Number(this._config.height) || 600;
    this.shadowRoot.innerHTML = `<style>${CSS}</style>
      <ha-card class="sf" style="--h:${h}px">
        <div class="surface loading">
          <aside class="lyrics-panel" aria-label="Liedtext">
            <div class="lyrics-copy"></div>
            <div class="lyrics-bar"></div>
          </aside>
          <header class="top">
            <span class="timer-badge" hidden>${svg("timer")}<span></span></span>
          </header>
          <section class="hero">
            <div class="flow">
              <button class="side prev" data-a="prev" aria-label="Vorheriger Titel"><img alt=""></button>
              <div class="art"><img alt="" hidden><span class="ph">${svg("note")}</span></div>
              <button class="side next" data-a="next" aria-label="Nächster Titel"><img alt=""></button>
            </div>
            <div class="caption">
              <div class="copy"><div class="title">&nbsp;</div><div class="sub">&nbsp;</div></div>
              <div class="actions">
                <button class="nb sm" data-a="speakers" aria-label="Lautsprecher oder Gruppe wählen" title="Lautsprecher / Gruppe">${svg("speaker")}</button>
                <button class="nb sm" data-a="like" aria-label="Lieblingssong">${svg("heartO")}</button>
                <button class="nb sm" data-a="queue" aria-label="Warteschlange">${svg("queue")}</button>
                <button class="nb sm" data-a="timer" aria-label="Sleep-Timer">${svg("timer")}</button>
                <button class="nb sm" data-a="eq" aria-label="Equalizer" title="Equalizer">${svg("eq")}</button>
                <button class="nb sm" data-a="history" aria-label="Zuletzt gehört">${svg("history")}</button>
              </div>
            </div>
          </section>
          <div class="progress">
            <span class="t cur">0:00</span>
            <div class="groove" role="slider" aria-label="Position" tabindex="0"><div class="fill"></div><div class="knob"></div></div>
            <span class="t dur">0:00</span>
          </div>
          <div class="transport">
            <button class="nb" data-a="lyrics" aria-label="Liedtext ein- oder ausblenden" title="Liedtext">${svg("lyrics")}</button>
            <button class="nb" data-a="shuffle" aria-label="Zufallswiedergabe" title="Zufallswiedergabe">${svg("shuffle")}</button>
            <button class="nb" data-a="prev" aria-label="Zurück">${svg("prev")}</button>
            <button class="nb main" data-a="playpause" aria-label="Wiedergabe">${svg("play")}</button>
            <button class="nb" data-a="next" aria-label="Weiter">${svg("next")}</button>
            <button class="nb" data-a="repeat" aria-label="Wiederholen" title="Wiederholen">${svg("repeat")}</button>
            <button class="nb" data-a="browse" aria-label="Titel, Alben und Playlists auswählen" title="Musik auswählen">${svg("browse")}</button>
          </div>
          <div class="volume">
            <button class="nb sm" data-a="mute" aria-label="Stumm">${svg("vol")}</button>
            <button class="nb xs" data-a="voldown" aria-label="Leiser">${svg("minus")}</button>
            <input type="range" min="0" max="100" step="1" value="0" aria-label="Lautstärke">
            <button class="nb xs" data-a="volup" aria-label="Lauter">${svg("plus")}</button>
            <span class="pct">0%</span>
          </div>
          <div class="sheet-wrap" hidden><div class="sheet" role="dialog" aria-modal="true"></div></div>
          <div class="toast" role="status"></div>
        </div>
      </ha-card>`;
    const root = this.shadowRoot;
    root.addEventListener("click", (ev) => this._click(ev));
    root.addEventListener("input", (ev) => this._input(ev));
    root.addEventListener("change", (ev) => this._change(ev));
    root.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && this._s.sheet) this._closeSheet();
      if (ev.key === "Enter" && ev.target.matches?.(".search-in")) this._runSearch(ev.target.value);
      if (ev.key === "Enter" && ev.target.matches?.(".pl-search-in")) this._runPlaylistSearch(ev.target.value);
    });
    const groove = this._$(".groove");
    groove.addEventListener("pointerdown", (ev) => this._seekStart(ev));
    this._layout();
  }

  _layout() {
    const surface = this._$(".surface");
    if (!surface) return;
    const w = this.clientWidth || surface.clientWidth || 0;
    surface.classList.toggle("wide", w >= 900);
    surface.classList.toggle("narrow", w > 0 && w < 520);
  }

  /* ------------------------------------------------------------ update */
  _update() {
    if (!this.shadowRoot || !this._hass) return;
    const st = this._st;
    const surface = this._$(".surface");
    if (!st) {
      surface.classList.remove("loading");
      surface.classList.add("ready", "unavailable");
      this._$(".title").textContent = `${this._config.entity} gibt es nicht`;
      this._$(".sub").textContent = "Integration „Spotify Flex Player“ einrichten oder entity in der Karte anpassen.";
      return;
    }
    surface.classList.remove("loading");
    surface.classList.toggle("unavailable", st.state === "unavailable");
    const a = st.attributes;
    const playing = st.state === "playing";
    this._trackSkew();
    const hasMedia = !!a.media_title;

    // header
    const speakers = (a.speakers || []);
    const spk = this._$('.actions [data-a="speakers"]');
    spk.classList.toggle("warn", !speakers.length);
    spk.title = speakers.length ? `Lautsprecher: ${a.source || speakers.join(", ")}` : "Kein Lautsprecher aktiv";
    const tb = this._$(".timer-badge");
    if (a.sleep_timer_ends) { tb.hidden = false; this._timerEnds = new Date(a.sleep_timer_ends).getTime(); }
    else { tb.hidden = true; this._timerEnds = null; }
    this._$(".top").classList.toggle("empty", !a.sleep_timer_ends);

    // cover + caption
    const art = a.entity_picture ? (a.entity_picture.startsWith("http") ? a.entity_picture : this._hass.hassUrl?.(a.entity_picture) || a.entity_picture) : null;
    const img = this._$(".art img");
    if (art !== this._s.lastArt) {
      if (this._s.lastArt) this._s.prevArt = this._s.lastArt;
      this._s.lastArt = art;
      this._tint(art ? (a.access_token ? this._hass.hassUrl?.(`/api/media_player_proxy/${this._config.entity}?token=${a.access_token}&cache=${encodeURIComponent(art.slice(-24))}`) : null) : null, art);
      if (art) { img.src = art; img.hidden = false; } else { img.removeAttribute("src"); img.hidden = true; }
    }
    this._$(".art .ph").hidden = !!art;
    this._$(".title").textContent = hasMedia ? a.media_title : (st.state === "unavailable" ? "Spotify Flex nicht erreichbar" : "Bereit");
    this._$(".sub").textContent = hasMedia ? [a.media_artist, a.media_album_name].filter(Boolean).join(" · ")
      : "Über das Noten-Symbol Musik auswählen";

    // transport
    const pp = this._$('[data-a="playpause"]');
    pp.innerHTML = svg(playing ? "pause" : "play");
    pp.setAttribute("aria-label", playing ? "Pause" : "Wiedergabe");
    this._$('[data-a="shuffle"]').classList.toggle("on", !!a.shuffle);
    const rep = this._$('[data-a="repeat"]');
    rep.classList.toggle("on", a.repeat && a.repeat !== "off");
    rep.innerHTML = svg(a.repeat === "one" ? "repeatOne" : "repeat");
    this._$('[data-a="lyrics"]').classList.toggle("on", this._s.lyricsOn && surface.classList.contains("wide"));

    // volume
    const vol = Math.round((a.volume_level ?? 0) * 100);
    const range = this._$(".volume input");
    if (!this._volDrag && this.shadowRoot.activeElement !== range) range.value = vol;
    range.style.setProperty("--p", `${range.value}%`);
    this._$(".pct").textContent = `${range.value}%`;
    this._$('[data-a="mute"]').innerHTML = svg(vol === 0 ? "volOff" : "vol");

    // side covers (cover flow) and liked state on track change
    const uri = a.media_content_id || null;
    if (uri !== this._s.trackUri) {
      this._s.trackUri = uri;
      this._s.liked = null;
      this._paintLike();
      if (uri && /^spotify:(track|episode):/.test(uri)) this._loadLike(uri);
      this._loadNext();
    }
    this._paintFlow();
    this._syncLyrics();
    this._frame();

    // lift the veil only once real data is known (no flash of an empty player)
    surface.classList.add("ready");
    if (this._s.sheet === "speakers") this._renderSpeakers();
    if (this._s.sheet === "queue" && this._s.queueKey !== uri) this._openQueue(true);
  }

  _paintFlow() {
    const on = this._config.cover_flow !== false;
    const prev = this._$(".side.prev"), next = this._$(".side.next");
    const set = (btn, src) => {
      const im = btn.querySelector("img");
      if (on && src) { if (im.getAttribute("src") !== src) im.src = src; btn.classList.add("has"); }
      else { im.removeAttribute("src"); btn.classList.remove("has"); }
    };
    set(prev, this._s.prevArt && this._s.prevArt !== this._s.lastArt ? this._s.prevArt : null);
    set(next, this._s.nextArt);
  }

  async _loadNext() {
    if (this._config.cover_flow === false || !this._st || !this._attrs.media_title) { this._s.nextArt = null; return; }
    const key = this._s.trackUri;
    try {
      const q = await this._resp("queue");
      if (key !== this._s.trackUri) return;
      this._s.nextArt = q.items?.[0]?.image || null;
      this._s.queueCache = q;
    } catch (_) { this._s.nextArt = null; }
    this._paintFlow();
  }

  _paintLike() {
    const b = this._$('[data-a="like"]');
    b.innerHTML = svg(this._s.liked ? "heart" : "heartO");
    b.classList.toggle("on", !!this._s.liked);
    b.disabled = !this._s.trackUri;
  }

  async _loadLike(uri) {
    try {
      const r = await this._resp("like", { action: "status", uri });
      if (uri === this._s.trackUri) { this._s.liked = !!r.liked; this._paintLike(); }
    } catch (_) { /* Bibliothek nicht verbunden */ }
  }

  /* --------------------------------------------- per-frame (progress, lyrics) */
  _frame() {
    if (!this._st || !this.shadowRoot) return;
    const a = this._attrs;
    const dur = Number(a.media_duration || 0);
    const pos = this._seeking != null ? this._seeking : this._position();
    const pct = dur ? Math.max(0, Math.min(100, (pos / dur) * 100)) : 0;
    const g = this._$(".groove");
    g.style.setProperty("--p", `${pct}%`);
    g.setAttribute("aria-valuenow", String(Math.round(pos)));
    this._$(".t.cur").textContent = fmt(pos);
    this._$(".t.dur").textContent = dur ? fmt(dur) : "0:00";
    if (this._timerEnds) {
      const left = Math.max(0, (this._timerEnds - Date.now()) / 1000);
      this._$(".timer-badge span").textContent = fmt(left);
    }
    this._lyricTick();
  }

  /* ------------------------------------------------------------ lyrics */
  _syncLyrics() {
    const a = this._attrs;
    const panelOn = this._s.lyricsOn;
    this._$(".surface").classList.toggle("lyrics-on", panelOn);
    const bar = this._$(".lyrics-bar");
    if (bar && !bar.firstChild) bar.innerHTML = this._offsetCtl();
    if (!a.media_title) { this._s.lyrics = null; this._s.lyricsKey = null; this._paintLyrics(); return; }
    const key = `${a.media_title}|${a.media_artist || ""}|${Math.round(a.media_duration || 0)}`;
    if (key === this._s.lyricsKey) return;
    this._s.lyricsKey = key;
    this._s.lyrics = { loading: true, lines: [], text: "" };
    this._paintLyrics();
    if (/:episode:/.test(a.media_content_id || "")) { this._s.lyrics = { lines: [], text: "" }; this._paintLyrics(); return; }
    const load = (attempt) => this._fetchLyrics(a).then((res) => {
      if (this._s.lyricsKey !== key) return;
      res.searching = !res.lines.length && !res.text && attempt < 2;
      this._s.lyrics = res; this._paintLyrics();
      // lrclib sucht unbekannte Titel beim ersten Abruf erst extern und meldet dann oft
      // „nicht gefunden“ – beim zweiten Abruf liegt der Text vor. Darum nachfragen.
      const wait = [6000, 20000][attempt];
      if (!res.lines.length && !res.text && wait) setTimeout(() => { if (this._s.lyricsKey === key) load(attempt + 1); }, wait);
    });
    load(0);
  }

  async _fetchLyrics(a) {
    const artist = String(a.media_artist || "").split(",")[0].trim();
    const params = new URLSearchParams({ track_name: a.media_title, artist_name: artist });
    if (a.media_album_name) params.set("album_name", a.media_album_name);
    if (a.media_duration) params.set("duration", String(Math.round(a.media_duration)));
    const get = async (url) => {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 15000); // hängende Abrufe nicht ewig warten lassen
      try {
        const r = await fetch(url, { signal: ctl.signal, headers: { "Lrclib-Client": `spotify-flex-flow ${CARD_VERSION}` } });
        if (!r.ok) return null;
        return await r.json();
      } catch (_) { return null; } finally { clearTimeout(t); }
    };
    let hit = await get(`https://lrclib.net/api/get?${params}`);
    if (!hit || (!hit.syncedLyrics && !hit.plainLyrics)) {
      const list = await get(`https://lrclib.net/api/search?${new URLSearchParams({ track_name: a.media_title, artist_name: artist })}`);
      if (Array.isArray(list) && list.length) {
        const dur = Number(a.media_duration || 0);
        hit = list.filter((x) => x.syncedLyrics).sort((x, y) => Math.abs((x.duration || 0) - dur) - Math.abs((y.duration || 0) - dur))[0] || list[0];
      }
    }
    const lines = parseLrc(hit?.syncedLyrics);
    return { lines, text: lines.length ? "" : String(hit?.plainLyrics || "").trim() };
  }

  _lyricsTargets() {
    return [this._$(".lyrics-panel .lyrics-copy"), this._s.sheet === "lyrics" ? this._$(".sheet .lyrics-copy") : null].filter(Boolean);
  }

  _paintLyrics() {
    const L = this._s.lyrics;
    for (const box of this._lyricsTargets()) {
      box.dataset.cur = "";
      if (box.dataset.key !== (this._s.lyricsKey || "")) box.scrollTop = 0;
      box.dataset.key = this._s.lyricsKey || "";
      if (!L) { box.innerHTML = `<p class="lmsg">Kein Titel aktiv.</p>`; continue; }
      if (L.loading || L.searching) { box.innerHTML = `<p class="lmsg">Liedtext wird ${L.searching ? "gesucht" : "geladen"} …</p>`; continue; }
      if (L.lines.length) {
        box.innerHTML = `<span class="ball" aria-hidden="true"></span>` + L.lines.map((l, i) =>
          `<div class="lyric-line" data-i="${i}">${l.words.map((w, k) => `<span class="w" data-k="${k}">${esc(w.w)}</span>`).join(" ")}</div>`).join("");
      } else if (L.text) box.innerHTML = `<div class="plain">${esc(L.text)}</div>`;
      else box.innerHTML = `<p class="lmsg">Für diesen Titel ist kein Liedtext verfügbar.</p>`;
    }
    this._lyricTick(true);
    this._ballLoop();
  }

  _heardMs() {
    // gehörte Position = Spotify-Position minus Puffer bis zum Lautsprecher
    return (this._position() - this._offset()) * 1000;
  }

  _lyricTick(force = false) {
    const L = this._s.lyrics;
    if (!L?.lines?.length) return;
    const ms = this._heardMs();
    let cur = -1;
    for (let i = 0; i < L.lines.length; i++) { if (L.lines[i].t <= ms) cur = i; else break; }
    for (const box of this._lyricsTargets()) {
      if (!force && box.dataset.cur === String(cur)) continue;
      box.dataset.cur = String(cur);
      box.querySelectorAll(".lyric-line").forEach((row, i) => {
        row.classList.toggle("current", i === cur);
        row.classList.toggle("past", i < cur);
      });
      const row = box.querySelector(`.lyric-line[data-i="${cur}"]`);
      if (row && box.clientHeight) this._glide(box, row.offsetTop - box.clientHeight / 2 + row.clientHeight / 2, force);
      else if (cur < 0) this._glide(box, 0, force);
    }
  }

  /* weiches Weiterrollen zur neuen Zeile (ease-in-out, ~0,7 s) */
  _glide(box, top, instant = false) {
    top = Math.max(0, Math.min(top, box.scrollHeight - box.clientHeight));
    if (box._glide) cancelAnimationFrame(box._glide);
    box._glide = null;
    if (instant || Math.abs(top - box.scrollTop) < 1) { box.scrollTop = top; return; }
    const from = box.scrollTop, dist = top - from, t0 = performance.now();
    const dur = Math.min(900, 520 + Math.abs(dist) * 1.2);
    const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
    const step = (now) => {
      const t = Math.min(1, (now - t0) / dur);
      box.scrollTop = from + dist * ease(t);
      box._glide = t < 1 ? requestAnimationFrame(step) : null;
    };
    box._glide = requestAnimationFrame(step);
  }

  /* springender Punkt (wie das Mitsing-Bällchen): landet auf jedem Wort, wenn es gesungen wird */
  _ballLoop() {
    if (this._raf) return;
    const step = () => {
      this._raf = null;
      if (!this.isConnected || !this._s.lyrics?.lines?.length) return;
      const boxes = this._lyricsTargets().filter((b) => b.clientHeight);
      if (!boxes.length) { this._raf = requestAnimationFrame(step); return; }
      const L = this._s.lyrics;
      const ms = this._heardMs();
      const playing = this._st?.state === "playing";
      let li = -1;
      for (let i = 0; i < L.lines.length; i++) { if (L.lines[i].t <= ms) li = i; else break; }
      this._lyricTick();
      for (const box of boxes) this._placeBall(box, L, li, ms, playing);
      this._raf = requestAnimationFrame(step);
    };
    this._raf = requestAnimationFrame(step);
  }

  _placeBall(box, L, li, ms, playing) {
    const ball = box.querySelector(".ball");
    if (!ball) return;
    const line = L.lines[li];
    const row = li >= 0 ? box.querySelector(`.lyric-line[data-i="${li}"]`) : null;
    const nextLine = L.lines[li + 1];
    const bridging = nextLine && nextLine.t - (line?.end ?? 0) < 4000;
    if (!line || !row || (ms > line.end + 700 && !bridging)) { ball.classList.remove("on"); return; }
    const spans = row.querySelectorAll(".w");
    const words = line.words;
    let k = 0;
    for (let i = 0; i < words.length; i++) { if (words[i].t <= ms) k = i; else break; }
    // echte Bildschirmlage (berücksichtigt die Vergrößerung der aktuellen Zeile), in Box-Koordinaten
    const br = box.getBoundingClientRect();
    const pos = (span) => { const r = span.getBoundingClientRect(); return { x: r.left - br.left + box.scrollLeft + r.width / 2, y: r.top - br.top + box.scrollTop }; };
    const a = spans[k] ? pos(spans[k]) : null;
    if (!a) { ball.classList.remove("on"); return; }
    let nextT = words[k + 1] ? words[k + 1].t : line.end;
    let startT = words[k].t;
    let b = spans[k + 1] ? pos(spans[k + 1]) : null;
    const nl = L.lines[li + 1];
    if (!b && nl && nl.words?.length && nl.t - words[k].t < 4000) {
      // letztes Wort: rechtzeitig zum ersten Wort der nächsten Zeile hinüberhüpfen
      const first = box.querySelector(`.lyric-line[data-i="${li + 1}"] .w`);
      if (first) {
        const lastDur = Math.max(250, Math.min(line.end - words[k].t, nl.t - words[k].t));
        const flight = Math.min(650, nl.t - words[k].t);
        const leave = Math.max(words[k].t + Math.min(lastDur, 450), nl.t - flight);
        if (ms >= leave) { b = pos(first); nextT = nl.t; startT = leave; }
      }
    }
    let p = (ms - startT) / Math.max(120, nextT - startT);
    p = Math.max(0, Math.min(1, p));
    let x = a.x, y = a.y;
    let lift = 0;
    if (b) {
      x = a.x + (b.x - a.x) * p;
      y = a.y + (b.y - a.y) * p;
      const hop = Math.min(16, 7 + Math.abs(b.x - a.x) * 0.12);
      lift = hop * 4 * p * (1 - p);
      if (b.y !== a.y) lift = Math.min(26, 12 + Math.abs(b.y - a.y) * 0.25) * 4 * p * (1 - p); // Zeilensprung: höherer Bogen
    } else {
      lift = 6 * 4 * p * (1 - p) * (p < 0.5 ? 1 : 0.4); // letzter Hüpfer auf dem letzten Wort
    }
    spans.forEach((s, i) => s.classList.toggle("sung", i <= k));
    ball.style.transform = `translate(${x - 5}px, ${y - 13 - lift}px)`;
    ball.classList.toggle("on", playing || ms <= line.end);
  }

  _setOffset(delta, absolute = null) {
    const v = absolute !== null ? absolute : this._offset() + delta;
    this._s.offset = Math.max(-3, Math.min(3, Math.round(v * 100) / 100));
    lsSet(this._ls + "fine", this._s.offset);
    this.shadowRoot.querySelectorAll(".offset-val").forEach((el) => { el.textContent = `${this._s.offset.toFixed(1).replace(".", ",")} s`; });
    this._lyricTick(true);
  }

  /* ----------------------------------------------- Hintergrund nach Cover-Farbe */
  _tint(proxyUrl, directUrl) {
    const token = (this._tintToken = (this._tintToken || 0) + 1);
    const reset = () => { if (token === this._tintToken) ["--sf-bg", "--sf-hi", "--sf-lo", "--sf-lo2"].forEach((v) => this.style.removeProperty(v)); };
    if (!directUrl) return reset();   // kein Cover: weiß
    const tryLoad = (urls) => {
      const url = urls.shift();
      if (!url) return reset();
      const im = new Image();
      if (!url.startsWith("/") && !url.startsWith(location.origin)) im.crossOrigin = "anonymous";
      im.onload = () => {
        if (token !== this._tintToken) return;
        try { this._applyTint(coverColor(im)); } catch (_) { tryLoad(urls); }  // Canvas gesperrt (CORS) -> nächste Quelle
      };
      im.onerror = () => tryLoad(urls);
      im.src = url;
    };
    tryLoad([proxyUrl, directUrl].filter(Boolean));
  }

  _applyTint(c) {
    if (!c) return;
    const [h, sat] = c;
    const S = sat < 0.1 ? 8 : Math.round(Math.min(62, 30 + sat * 55));   // Graustufen-Cover -> zartes Grau
    const st = this.style;
    st.setProperty("--sf-bg", `hsl(${h} ${S}% 87%)`);
    st.setProperty("--sf-hi", `hsl(${h} ${Math.min(100, S + 10)}% 95%)`);
    st.setProperty("--sf-lo", `hsl(${h} ${Math.round(S * 0.7)}% 76%)`);
    st.setProperty("--sf-lo2", `hsl(${h} ${Math.round(S * 0.65)}% 70%)`);
  }

  /* ------------------------------------------------------------- input */
  _click(ev) {
    const btn = ev.target.closest("[data-a]");
    if (!btn || btn.disabled) {
      if (ev.target.classList?.contains("sheet-wrap")) this._closeSheet();
      return;
    }
    const a = btn.dataset.a;
    const attrs = this._attrs;
    switch (a) {
      case "playpause": return this._once("pp", () => this._player(this._st?.state === "playing" ? "media_pause" : "media_play"));
      case "prev": return this._once("prev", () => this._player("media_previous_track"));
      case "next": return this._once("next", () => this._player("media_next_track"));
      case "shuffle": return this._once("sh", () => this._player("shuffle_set", { shuffle: !attrs.shuffle }));
      case "repeat": {
        const nx = { off: "all", all: "one", one: "off" }[attrs.repeat || "off"] || "off";
        return this._once("rp", () => this._player("repeat_set", { repeat: nx }));
      }
      case "volup": case "voldown": {
        const v = Math.max(0, Math.min(1, (attrs.volume_level || 0) + (a === "volup" ? 0.05 : -0.05)));
        return this._once("vol", () => this._player("volume_set", { volume_level: Math.round(v * 100) / 100 }));
      }
      case "mute": {
        const v = attrs.volume_level || 0;
        if (v > 0) { this._s.unmute = v; return this._once("vol", () => this._player("volume_set", { volume_level: 0 })); }
        return this._once("vol", () => this._player("volume_set", { volume_level: this._s.unmute || 0.3 }));
      }
      case "lyrics":
        if (!this._$(".surface").classList.contains("wide")) return this._openLyrics();
        this._s.lyricsOn = !this._s.lyricsOn; lsSet(this._ls + "lyrics", this._s.lyricsOn);
        this._$('[data-a="lyrics"]').classList.toggle("on", this._s.lyricsOn);
        this._syncLyrics(); this._paintLyrics();
        return;
      case "browse": return this._openLibrary();
      case "history": this._s.lib.tab = "recent"; this._s.lib.stack = []; return this._openLibrary(true);
      case "like": return this._once("like", async () => {
        const r = await this._resp("like", { action: "toggle", uri: this._s.trackUri });
        this._s.liked = !!r.liked; this._paintLike();
        this._toast(r.liked ? "Zu Lieblingssongs hinzugefügt" : "Aus Lieblingssongs entfernt");
      });
      case "queue": return this._openQueue();
      case "timer": return this._openTimer();
      case "speakers": return this._openSpeakers();
      case "eq": return this._openEq();
      case "eq-toggle": return this._eqChange({ enabled: !this._s.eq.enabled }, true);
      case "eq-preset": {
        const p = this._s.eq.presets.find((x) => x.id === btn.dataset.id);
        Object.assign(this._s.eq, { preset: p.id, gains: p.gains.slice(), enabled: true });
        this._renderEq();
        return this._eqSend({ preset: p.id }, true);
      }
      case "close": return this._closeSheet();
      case "off-minus": return this._setOffset(-0.1);
      case "off-plus": return this._setOffset(0.1);
      // library sheet
      case "tab": this._s.lib.tab = btn.dataset.tab; this._s.lib.stack = []; return this._renderLibrary();
      case "lib-back": this._s.lib.stack.pop(); return this._renderLibrary();
      case "view": this._s.lib.view = this._s.lib.view === "grid" ? "list" : "grid"; lsSet(this._ls + "view", this._s.lib.view); return this._renderLibrary(true);
      case "open": this._s.lib.stack.push({ id: btn.dataset.id, title: btn.dataset.title }); return this._renderLibrary();
      case "more": return this._renderLibrary(false, btn.dataset.id);
      case "play": return this._playItem(btn.dataset.id, btn.dataset.title);
      case "play-all": return this._playItem(btn.dataset.id, btn.dataset.title, btn.dataset.shuffle === "1");
      case "item-menu": return this._itemMenu(btn);
      case "enqueue": return this._once("enq", async () => {
        await this._svc(DOMAIN, "add_to_queue", { uri: btn.dataset.uri });
        this._closeMenu(); this._toast("Zur Warteschlange hinzugefügt");
      });
      case "do-search": return this._runSearch(this._$(".search-in")?.value || "");
      case "pl-search": return this._runPlaylistSearch(this._$(".pl-search-in")?.value || "");
      case "pl-clear": this._s.lib.plResults = null; this._s.lib.plQuery = ""; return this._renderLibrary();
      case "pl-follow": return this._once("plf", async () => {
        const r = await this._resp("like", { action: "save", uri: btn.dataset.uri });
        if (!r.liked) throw new Error("Spotify hat die Playlist nicht gespeichert.");
        (this._s.lib.saved ||= new Set()).add(btn.dataset.uri);
        this._closeMenu();
        this._toast(`„${btn.dataset.title}“ ist jetzt in deinen Playlists`);
        this._renderLibrary();
      });
      // speakers sheet
      case "spk": return this._once("spk" + btn.dataset.id, async () => {
        const st = this._hass.states[btn.dataset.id];
        await this._svc("media_player", st?.state === "off" ? "turn_on" : "turn_off", { entity_id: btn.dataset.id });
      });
      case "only": return this._once("only", () => this._player("select_source", { source: btn.dataset.name }));
      case "group": return this._once("grp", async () => {
        const g = this._groupEntity();
        if (g) await this._svc("select", "select_option", { entity_id: g.entity_id, option: btn.dataset.opt });
      });
      // timer sheet
      case "sleep": return this._once("sleep", async () => {
        const min = Number(btn.dataset.min);
        await this._resp("sleep_timer", { minutes: min });
        this._toast(min ? `Wiedergabe stoppt in ${min} Minuten` : "Sleep-Timer aus");
        this._closeSheet();
      });
      default: return undefined;
    }
  }

  _input(ev) {
    const t = ev.target;
    if (t.matches(".volume input")) {
      this._volDrag = true;
      t.style.setProperty("--p", `${t.value}%`);
      this._$(".pct").textContent = `${t.value}%`;
    } else if (t.matches(".spk-vol")) {
      t.style.setProperty("--p", `${t.value}%`);
      const pct = t.closest(".spk-card")?.querySelector(".spk-pct");
      if (pct) pct.textContent = `${t.value}%`;
    }
  }

  _change(ev) {
    const t = ev.target;
    if (t.matches(".volume input")) {
      this._volDrag = false;
      this._once("vol", () => this._player("volume_set", { volume_level: Number(t.value) / 100 }));
    } else if (t.matches(".spk-vol")) {
      this._once("sv" + t.dataset.id, () => this._svc("media_player", "volume_set", { entity_id: t.dataset.id, volume_level: Number(t.value) / 100 }));
    }
  }

  _seekStart(ev) {
    const dur = Number(this._attrs.media_duration || 0);
    if (!dur) return;
    const g = ev.currentTarget;
    const at = (e) => { const r = g.getBoundingClientRect(); return Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * dur; };
    g.setPointerCapture?.(ev.pointerId);
    this._seeking = at(ev); this._frame();
    const move = (e) => { this._seeking = at(e); this._frame(); };
    const up = (e) => {
      g.removeEventListener("pointermove", move); g.removeEventListener("pointerup", up); g.removeEventListener("pointercancel", up);
      const target = at(e); this._seeking = null;
      this._once("seek", () => this._player("media_seek", { seek_position: Math.round(target) }));
    };
    g.addEventListener("pointermove", move); g.addEventListener("pointerup", up); g.addEventListener("pointercancel", up);
  }

  /* ------------------------------------------------------------ sheets */
  _sheet(name, html, cls = "") {
    this._s.sheet = name;
    const wrap = this._$(".sheet-wrap");
    const sheet = this._$(".sheet");
    sheet.className = `sheet ${cls}`;
    sheet.innerHTML = html;
    wrap.hidden = false;
    requestAnimationFrame(() => wrap.classList.add("open"));
  }

  _closeSheet() {
    this._s.sheet = null;
    const wrap = this._$(".sheet-wrap");
    wrap.classList.remove("open");
    wrap.hidden = true;
    this._$(".sheet").innerHTML = "";
  }

  _head(title, icon, extra = "") {
    return `<div class="sh-head"><span class="sh-title">${svg(icon)}<span>${esc(title)}</span></span>${extra}<button class="nb sm" data-a="close" aria-label="Schließen">${svg("close")}</button></div>`;
  }

  /* lyrics (narrow screens) */
  _openLyrics() {
    const a = this._attrs;
    this._sheet("lyrics", `${this._head(a.media_title || "Liedtext", "lyrics")}
      <div class="sh-sub">${esc([a.media_artist, a.media_album_name].filter(Boolean).join(" · "))}</div>
      <div class="sh-sub">${this._offsetCtl()}</div>
      <div class="lyrics-copy big"></div>`, "tall");
    this._paintLyrics();
  }

  _offsetCtl() {
    return `<span class="offset" title="Feinkorrektur – die Audio-Verzögerung wird automatisch gemessen">
      <button class="nb xs" data-a="off-minus" aria-label="Liedtext früher">${svg("minus")}</button>
      <span class="offset-val">${this._offset().toFixed(1).replace(".", ",")} s</span>
      <button class="nb xs" data-a="off-plus" aria-label="Liedtext später">${svg("plus")}</button></span>`;
  }

  /* speakers */
  _openSpeakers() { this._sheet("speakers", ""); this._renderSpeakers(); }

  _renderSpeakers() {
    const g = this._groupEntity();
    const opts = (g?.attributes?.options || []).filter((o) => o);
    const chips = opts.map((o) => `<button class="gchip ${g.state === o ? "on" : ""}" data-a="group" data-opt="${esc(o)}">${o === "Aus" ? svg("power") : svg("speaker")}<span>${esc(o)}</span></button>`).join("");
    const cards = this._speakers().map((st) => {
      const on = st.state !== "off" && st.state !== "unavailable";
      const v = Math.round((st.attributes.volume_level ?? 0) * 100);
      return `<div class="spk-card ${on ? "on" : ""} ${st.state === "unavailable" ? "na" : ""}">
        <button class="spk-main" data-a="spk" data-id="${esc(st.entity_id)}" ${st.state === "unavailable" ? "disabled" : ""}>
          <span class="spk-ic">${svg("speaker")}</span>
          <span class="spk-txt"><span class="spk-name">${esc(this._speakerName(st))}</span>
          <span class="spk-state">${st.state === "unavailable" ? "nicht erreichbar" : on ? (st.state === "playing" ? "spielt" : "aktiv") : "aus"}</span></span>
          <span class="switch ${on ? "on" : ""}" aria-hidden="true"></span>
        </button>
        <div class="spk-btns"><button class="pill xs ${this._attrs.source === this._speakerName(st) ? "on" : ""}" data-a="only" data-name="${esc(this._speakerName(st))}" ${st.state === "unavailable" ? "disabled" : ""}>Nur hier</button></div>
        ${on ? `<div class="spk-volrow">${svg("vol")}<input class="spk-vol" type="range" min="0" max="100" value="${v}" style="--p:${v}%" data-id="${esc(st.entity_id)}" aria-label="Lautstärke ${esc(this._speakerName(st))}"><span class="spk-pct">${v}%</span></div>` : ""}
      </div>`;
    }).join("");
    const html = `${this._head("Lautsprecher & Gruppen", "speaker")}
      ${chips ? `<h4 class="grp">Gruppen</h4><div class="gchips">${chips}</div>` : ""}
      <h4 class="grp">Lautsprecher</h4>
      <div class="spk-grid">${cards || `<p class="lmsg">Keine Spotify-Flex-Lautsprecher gefunden.</p>`}</div>
      <p class="hint">„Nur hier“ spielt nur auf dieser Box, der Schalter nimmt eine Box dazu oder heraus. Gruppen legst du in der Spotify-Flex-App an (mehrere Boxen einschalten → „+ Auswahl als Gruppe“).</p>`;
    const sheet = this._$(".sheet");
    if (this._s.sheet !== "speakers") return;
    if (sheet.contains(this.shadowRoot.activeElement) && this.shadowRoot.activeElement?.matches?.(".spk-vol")) return;
    sheet.innerHTML = html;
  }

  /* equalizer */
  async _openEq() {
    this._sheet("eq", `${this._head("Equalizer", "eq")}<p class="lmsg">Wird geladen …</p>`);
    try {
      this._s.eq = await this._resp("equalizer");
      this._eqMark();
      if (this._s.sheet === "eq") this._renderEq();
    } catch (err) {
      const msg = /not found|nicht gefunden|Unknown service|unknown/i.test(err?.message || "")
        ? "Für den Equalizer Home Assistant einmal neu starten (neue Version der Integration)."
        : (err?.message || String(err));
      if (this._s.sheet === "eq") this._$(".sheet .lmsg").textContent = msg;
    }
  }

  _eqMark() {
    this._$('.actions [data-a="eq"]')?.classList.toggle("on", !!this._s.eq?.enabled);
  }

  _renderEq() {
    const e = this._s.eq;
    if (!e || this._s.sheet !== "eq") return;
    const name = !e.enabled ? "Aus" : e.preset === "custom" ? "Eigene Einstellung" : (e.presets.find((p) => p.id === e.preset) || {}).name || "";
    this._$(".sheet").innerHTML = `${this._head("Equalizer", "eq", `<button class="switch ${e.enabled ? "on" : ""}" data-a="eq-toggle" role="switch" aria-checked="${!!e.enabled}" aria-label="Equalizer an oder aus"></button>`)}
      <div class="eq-wrap"></div>
      <div class="eq-name">${esc(name)}</div>
      <div class="gchips eq-presets">${e.presets.map((p) => `<button class="gchip ${e.enabled && e.preset === p.id ? "on" : ""}" data-a="eq-preset" data-id="${esc(p.id)}">${esc(p.name)}</button>`).join("")}</div>
      <p class="hint center">Punkte ziehen oder Voreinstellung wählen – wirkt sofort auf allen Lautsprechern.</p>`;
    this._drawEq();
    const wrap = this._$(".eq-wrap");
    wrap.addEventListener("pointerdown", (ev) => this._eqDown(ev));
    wrap.addEventListener("keydown", (ev) => this._eqKey(ev));
    this._eqMark();
  }

  _eqGeo() {
    const wrap = this._$(".eq-wrap");
    const w = Math.max(260, Math.round(wrap?.clientWidth || 600));
    return { w, h: 200, l: 30, r: 22, t: 24, b: 40 };
  }

  _drawEq() {
    const e = this._s.eq, wrap = this._$(".eq-wrap");
    if (!e || !wrap) return;
    const G = this._eqGeo(), n = e.bands.length, max = e.max;
    const X = (i) => G.l + (i * (G.w - G.l - G.r)) / (n - 1);
    const Y = (g) => G.t + ((max - g) * (G.h - G.t - G.b)) / (2 * max);
    const pts = e.gains.map((g, i) => [X(i), Y(g)]);
    let d = `M${pts[0][0]},${pts[0][1]}`;
    for (let i = 0; i < n - 1; i++) {
      const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
      d += ` C${p1[0] + (p2[0] - p0[0]) / 6},${p1[1] + (p2[1] - p0[1]) / 6} ${p2[0] - (p3[0] - p1[0]) / 6},${p2[1] - (p3[1] - p1[1]) / 6} ${p2[0]},${p2[1]}`;
    }
    const base = G.h - G.b;
    const hz = (f) => (f >= 1000 ? `${String(f / 1000).replace(".", ",")}k` : `${f}`);
    const db = (g) => `${g > 0 ? "+" : ""}${String(g).replace(".", ",")} dB`;
    const drag = this._s.eqDrag;
    wrap.innerHTML = `<svg class="eq-svg ${e.enabled ? "" : "off"}" viewBox="0 0 ${G.w} ${G.h}" width="${G.w}" height="${G.h}">
      <defs><linearGradient id="sf-eq-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="var(--acc)" stop-opacity=".28"/><stop offset="1" stop-color="var(--acc)" stop-opacity="0"/></linearGradient></defs>
      ${[max, 0, -max].map((g) => `<line class="eq-grid ${g === 0 ? "zero" : ""}" x1="${G.l}" x2="${G.w - G.r}" y1="${Y(g)}" y2="${Y(g)}"/><text class="eq-lbl" x="2" y="${Y(g) + 4}">${g > 0 ? "+" : g < 0 ? "−" : ""}${Math.abs(g)}</text>`).join("")}
      <path class="eq-area" d="${d} L${pts[n - 1][0]},${base} L${pts[0][0]},${base} Z"/>
      <path class="eq-curve" d="${d}"/>
      ${pts.map(([x, y], i) => `<g class="eq-dot ${drag === i ? "active" : ""}" data-band="${i}" tabindex="0" role="slider" aria-label="${hz(e.bands[i])} Hz" aria-valuemin="${-max}" aria-valuemax="${max}" aria-valuenow="${e.gains[i]}" aria-valuetext="${db(e.gains[i])}">
        <circle class="eq-knob" cx="${x}" cy="${y}" r="${drag === i ? 11 : 8}"/>
        ${drag === i ? `<text class="eq-val" x="${x}" y="${Math.max(13, y - 15)}">${db(e.gains[i])}</text>` : ""}
        <text class="eq-hz" x="${x}" y="${G.h - 14}">${hz(e.bands[i])}</text></g>`).join("")}
    </svg>`;
    this._eqX = X; this._eqG = G;
  }

  _eqPoint(ev) {
    const svgEl = this._$(".eq-svg"), r = svgEl.getBoundingClientRect(), G = this._eqG, e = this._s.eq;
    const x = ((ev.clientX - r.left) / r.width) * G.w, y = ((ev.clientY - r.top) / r.height) * G.h;
    let band = 0;
    for (let i = 1; i < e.bands.length; i++) if (Math.abs(this._eqX(i) - x) < Math.abs(this._eqX(band) - x)) band = i;
    const g = e.max - ((y - G.t) * 2 * e.max) / (G.h - G.t - G.b);
    return { band, gain: Math.round(Math.max(-e.max, Math.min(e.max, g)) * 2) / 2 };
  }

  _eqSet(band, gain) {
    const e = this._s.eq;
    if (e.gains[band] === gain && e.enabled) return;
    e.gains = e.gains.map((g, i) => (i === band ? gain : g));
    const ch = { gains: e.gains };
    if (!e.enabled) { e.enabled = true; ch.enabled = true; }
    this._eqSend(ch);
  }

  _eqDown(ev) {
    if (!ev.target.closest(".eq-svg") || !this._s.eq) return;
    ev.preventDefault();
    const wrap = this._$(".eq-wrap");
    wrap.setPointerCapture?.(ev.pointerId);
    const p = this._eqPoint(ev);
    this._s.eqDrag = p.band;
    this._eqSet(p.band, p.gain); this._drawEq();
    const move = (e2) => { const q = this._eqPoint(e2); this._eqSet(this._s.eqDrag, q.gain); this._drawEq(); };
    const up = () => {
      wrap.removeEventListener("pointermove", move); wrap.removeEventListener("pointerup", up); wrap.removeEventListener("pointercancel", up);
      this._s.eqDrag = null;
      this._eqSend({}, true);
    };
    wrap.addEventListener("pointermove", move); wrap.addEventListener("pointerup", up); wrap.addEventListener("pointercancel", up);
  }

  _eqKey(ev) {
    const dot = ev.target.closest?.(".eq-dot");
    if (!dot) return;
    const step = { ArrowUp: 0.5, ArrowRight: 0.5, ArrowDown: -0.5, ArrowLeft: -0.5, PageUp: 3, PageDown: -3 }[ev.key];
    if (step === undefined && ev.key !== "Home") return;
    ev.preventDefault();
    const band = Number(dot.dataset.band), max = this._s.eq.max;
    this._eqSet(band, ev.key === "Home" ? 0 : Math.max(-max, Math.min(max, this._s.eq.gains[band] + step)));
    this._drawEq();
    this._$(`.eq-dot[data-band="${band}"]`)?.focus({ preventScroll: true });
  }

  _eqChange(changes, now) {
    Object.assign(this._s.eq, changes);
    this._renderEq();
    return this._eqSend(changes, now);
  }

  _eqSend(changes, now = false) {
    this._eqPending = { ...(this._eqPending || {}), ...changes };
    clearTimeout(this._eqTimer);
    const go = async () => {
      const body = this._eqPending; this._eqPending = null;
      if (!body || !Object.keys(body).length) { if (this._s.eqDrag === null) this._renderEq(); return; }
      try {
        const r = await this._resp("equalizer", body);
        if (this._s.eqDrag === null) { this._s.eq = r; this._renderEq(); } else this._s.eq.preset = r.preset;
        this._eqMark();
      } catch (err) { this._toast(err?.message || String(err), true); }
    };
    if (now) return go();
    this._eqTimer = setTimeout(go, 150);
    return undefined;
  }

  /* timer */
  _openTimer() {
    const ends = this._timerEnds;
    const items = [15, 30, 45, 60, 90, 120].map((m) => `<button class="pill" data-a="sleep" data-min="${m}">${m} min</button>`).join("");
    this._sheet("timer", `${this._head("Sleep-Timer", "timer")}
      <p class="hint center">${ends ? `Läuft – Wiedergabe stoppt um ${new Date(ends).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })} Uhr.` : "Wiedergabe nach einer Zeit automatisch pausieren."}</p>
      <div class="pills">${items}</div>
      ${ends ? `<div class="pills"><button class="pill off" data-a="sleep" data-min="0">${svg("power")} Timer aus</button></div>` : ""}`, "small");
  }

  /* queue */
  async _openQueue(refresh = false) {
    if (!refresh) this._sheet("queue", `${this._head("Warteschlange", "queue")}<div class="list"><p class="lmsg">Wird geladen …</p></div>`);
    this._s.queueKey = this._s.trackUri;
    try {
      const q = await this._resp("queue");
      if (this._s.sheet !== "queue") return;
      const rows = [];
      if (q.current) rows.push(this._row(q.current, "current"));
      (q.items || []).forEach((it) => rows.push(this._row(it)));
      this._$(".sheet .list").innerHTML = rows.join("") || `<p class="lmsg">Die Warteschlange ist leer.</p>`;
    } catch (err) {
      const l = this._$(".sheet .list");
      if (l) l.innerHTML = `<p class="lmsg err">${esc(err.message || err)}</p>`;
    }
  }

  /* library */
  _openLibrary(keep = false) {
    if (!keep && !this._s.lib.tab) this._s.lib.tab = "playlists";
    this._sheet("library", `<div class="lib">
        <div class="lib-head"></div>
        <div class="lib-body"></div>
        <nav class="tabs">${TABS.map((t) => `<button class="tab" data-a="tab" data-tab="${t.id}" aria-label="${t.label}" title="${t.label}">${svg(t.icon)}<span>${t.label}</span></button>`).join("")}</nav>
      </div>`, "tall");
    this._renderLibrary();
  }

  async _renderLibrary(onlyView = false, moreId = null) {
    const lib = this._s.lib;
    const tab = TABS.find((t) => t.id === lib.tab) || TABS[1];
    const sheet = this._$(".sheet");
    if (this._s.sheet !== "library") return;
    sheet.querySelectorAll(".tab").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab.id));
    const top = lib.stack[lib.stack.length - 1];
    const title = top ? top.title : tab.label;
    sheet.querySelector(".lib-head").innerHTML = `<div class="sh-head">
        ${top ? `<button class="nb sm" data-a="lib-back" aria-label="Zurück">${svg("back")}</button>` : ""}
        <span class="sh-title">${svg(top ? "playlist" : tab.icon)}<span>${esc(title)}</span></span>
        <button class="nb sm" data-a="view" aria-label="Ansicht wechseln">${svg(lib.view === "grid" ? "list" : "grid")}</button>
        <button class="nb sm" data-a="close" aria-label="Schließen">${svg("close")}</button></div>
      ${tab.id === "playlists" && !top ? `<div class="search"><input class="pl-search-in search-in-pl" type="search" placeholder="Öffentliche Playlists suchen …" value="${esc(lib.plQuery || "")}" aria-label="Öffentliche Playlists suchen"><button class="nb sm" data-a="pl-search" aria-label="Playlists suchen">${svg("search")}</button>${lib.plResults ? `<button class="nb sm" data-a="pl-clear" aria-label="Suche schließen">${svg("close")}</button>` : ""}</div>` : ""}
      ${tab.id === "search" && !top ? `<div class="search"><input class="search-in" type="search" placeholder="Titel, Künstler, Alben, Playlists …" value="${esc(lib.query)}" aria-label="Suchbegriff"><button class="nb sm" data-a="do-search" aria-label="Suchen">${svg("search")}</button></div>` : ""}`;
    const body = sheet.querySelector(".lib-body");
    body.className = `lib-body ${lib.view}`;
    if (onlyView && this._s.libItems) { body.innerHTML = this._s.libItems; return; }
    if (tab.id === "search" && !top) {
      if (lib.results) { body.innerHTML = this._searchHtml(lib.results); this._s.libItems = body.innerHTML; }
      else body.innerHTML = `<p class="lmsg">Suchbegriff eingeben und Enter drücken.</p>`;
      setTimeout(() => sheet.querySelector(".search-in")?.focus(), 50);
      return;
    }
    const id = moreId || (top ? top.id : `${NODE}${tab.node}@0`);
    if (!moreId) body.innerHTML = `<p class="lmsg">Wird geladen …</p>`;
    try {
      const res = await this._hass.callWS({ type: "media_player/browse_media", entity_id: this._config.entity, media_content_id: id, media_content_type: "directory" });
      if (this._s.sheet !== "library") return;
      const items = (res.children || []).filter((c) => !(c.title === "Mehr …" && c.can_expand && !c.can_play));
      const more = (res.children || []).find((c) => c.title === "Mehr …" && c.can_expand && !c.can_play);
      const html = items.map((c) => this._row({
        title: c.title, subtitle: "", image: c.thumbnail,
        type: c.media_class, play_id: c.can_play ? c.media_content_id : null,
        browse_id: c.can_expand ? c.media_content_id.split("#")[0] : null,
        uri: c.can_play && !c.can_expand ? c.media_content_id.split("|")[0] : null,
      })).join("");
      const moreBtn = more ? `<button class="more-btn" data-a="more" data-id="${esc(more.media_content_id)}">Mehr laden</button>` : "";
      const head = top && /#spotify:/.test(top.id) ? `<div class="play-row">
          <button class="pill play-all" data-a="play-all" data-shuffle="0" data-id="${esc(top.id)}" data-title="${esc(top.title)}">${svg("play")} Alles abspielen</button>
          <button class="pill play-all" data-a="play-all" data-shuffle="1" data-id="${esc(top.id)}" data-title="${esc(top.title)}">${svg("shuffle")} Zufällig abspielen</button></div>` : "";
      if (moreId) {
        body.querySelector(".more-btn")?.remove();
        body.insertAdjacentHTML("beforeend", html + moreBtn);
      } else {
        const found = tab.id === "playlists" && !top && lib.plResults ? this._playlistResultsHtml(lib.plResults) : "";
        body.innerHTML = (found + (found ? `<h4 class="grp">Meine Playlists</h4>` : "") + head + html + moreBtn) || `<p class="lmsg">Hier ist nichts.</p>`;
      }
      this._s.libItems = body.innerHTML;
    } catch (err) {
      body.innerHTML = `<p class="lmsg err">${esc(err.message || err)}</p>`;
    }
  }

  async _runSearch(q) {
    q = String(q || "").trim();
    if (!q) return;
    const lib = this._s.lib;
    lib.query = q;
    const link = spotifyLink(q);
    if (link) {
      lib.results = { groups: [{ type: link.type, items: [this._linkResult(link)] }] };
      const b = this._$(".sheet .lib-body");
      if (b) { b.innerHTML = this._searchHtml(lib.results); this._s.libItems = b.innerHTML; }
      return;
    }
    const body = this._$(".sheet .lib-body");
    if (body) body.innerHTML = `<p class="lmsg">Suche „${esc(q)}“ …</p>`;
    await this._once("search", async () => {
      lib.results = await this._resp("search", { query: q, types: ["track", "artist", "album", "playlist", "show"] });
      if (this._s.sheet === "library" && lib.tab === "search") {
        const b = this._$(".sheet .lib-body");
        b.innerHTML = this._searchHtml(lib.results);
        this._s.libItems = b.innerHTML;
      }
    });
  }

  _linkResult(link) {
    const names = { playlist: "Playlist", album: "Album", track: "Titel", artist: "Künstler", show: "Podcast", episode: "Folge" };
    return { title: `${names[link.type]} aus Spotify-Link abspielen`, subtitle: link.uri, image: null, type: link.type,
      uri: link.uri, play_id: link.uri, browse_id: null };
  }

  async _runPlaylistSearch(q) {
    q = String(q || "").trim();
    if (!q) return;
    const lib = this._s.lib;
    lib.plQuery = q;
    const link = spotifyLink(q);
    if (link) { lib.plResults = [this._linkResult(link)]; return this._renderLibrary(); }
    await this._once("plsearch", async () => {
      const res = await this._resp("search", { query: q, types: ["playlist"] });
      lib.plResults = (res.groups || []).flatMap((g) => g.items);
      if (this._s.sheet === "library" && lib.tab === "playlists") await this._renderLibrary();
    });
  }

  _playlistResultsHtml(items) {
    const saved = this._s.lib.saved || new Set();
    const rows = items.map((it) => this._row(it, "", saved.has(it.uri) ? "saved" : "follow")).join("");
    return `<h4 class="grp">Öffentliche Playlists</h4>${rows || `<p class="lmsg">Keine Playlist gefunden.</p>`}
      <p class="hint">Spotify-eigene Playlists wie „This Is …“ oder Mixe gibt Spotify hier nicht heraus. In der Spotify-App über „Teilen → Link kopieren“ den Link holen und hier einfügen – dann lässt sie sich abspielen.</p>`;
  }

  _searchHtml(res) {
    const names = { track: "Titel", artist: "Künstler", album: "Alben", playlist: "Playlists", show: "Podcasts", episode: "Folgen", audiobook: "Hörbücher" };
    const groups = res?.groups || [];
    if (!groups.length) return `<p class="lmsg">Nichts gefunden.</p>`;
    return groups.map((g) => `<h4 class="grp">${esc(names[g.type] || g.type)}</h4>${g.items.map((it) => this._row(it)).join("")}`).join("");
  }

  _row(it, extra = "", follow = "") {
    const icon = { track: "note", episode: "podcast", album: "album", artist: "artist", playlist: "playlist", show: "podcast", podcast: "podcast", directory: "playlist" }[it.type] || "note";
    const open = it.browse_id ? `data-a="open" data-id="${esc(it.browse_id + (it.play_id && it.play_id.includes("#") ? "#" + it.play_id.split("#")[1] : ""))}" data-title="${esc(it.title)}"`
      : it.play_id ? `data-a="play" data-id="${esc(it.play_id)}" data-title="${esc(it.title)}"` : "";
    const canQueue = it.uri && /^spotify:(track|episode):/.test(it.uri);
    const menu = (it.play_id || canQueue) && extra !== "current"
      ? `<button class="nb xs dots" data-a="item-menu" data-id="${esc(it.play_id || "")}" data-uri="${esc(canQueue ? it.uri : "")}" data-pl="${esc(follow === "follow" && it.uri ? it.uri : "")}" data-title="${esc(it.title)}" aria-label="Mehr zu ${esc(it.title)}">${svg("dots")}</button>` : "";
    const badge = follow === "saved" ? `<span class="saved-badge" title="In deinen Playlists">${svg("heart")}</span>` : "";
    return `<div class="item ${extra}">
      <button class="item-main" ${open}>
        <span class="thumb ${it.type === "artist" ? "round" : ""}">${it.image ? `<img loading="lazy" alt="" src="${esc(it.image)}">` : svg(icon)}</span>
        <span class="item-txt"><span class="item-t">${esc(it.title)}</span>${it.subtitle ? `<span class="item-s">${esc(it.subtitle)}</span>` : ""}</span>
      </button>${badge}${menu}</div>`;
  }

  _itemMenu(btn) {
    this._closeMenu();
    const m = document.createElement("div");
    m.className = "menu";
    m.innerHTML = `${btn.dataset.id ? `<button data-a="play" data-id="${esc(btn.dataset.id)}" data-title="${esc(btn.dataset.title)}">${svg("play")}<span>Abspielen</span></button>` : ""}
      ${btn.dataset.uri ? `<button data-a="enqueue" data-uri="${esc(btn.dataset.uri)}">${svg("queueAdd")}<span>Zur Warteschlange</span></button>` : ""}
      ${btn.dataset.pl ? `<button data-a="pl-follow" data-uri="${esc(btn.dataset.pl)}" data-title="${esc(btn.dataset.title)}">${svg("heartO")}<span>Zu meinen Playlists</span></button>` : ""}`;
    const item = btn.closest(".item");
    item.append(m);
    this._menuEl = m;
    setTimeout(() => {
      this._menuOff = (e) => { if (!e.composedPath().includes(m)) this._closeMenu(); };
      this.shadowRoot.addEventListener("pointerdown", this._menuOff, { once: true });
    });
  }

  _closeMenu() { this._menuEl?.remove(); this._menuEl = null; }

  async _playItem(id, title, shuffle = null) {
    if (!id) return;
    await this._once("play", async () => {
      // Zufallswiedergabe vorher setzen: der Empfänger startet dann mit einem zufälligen Titel
      if (shuffle !== null) await this._player("shuffle_set", { shuffle });
      await this._svc("media_player", "play_media", { entity_id: this._config.entity, media_content_id: id, media_content_type: "music" });
      // war vorher noch nichts geladen, greift die Einstellung erst jetzt
      if (shuffle) await this._player("shuffle_set", { shuffle: true });
      this._closeMenu();
      this._toast(shuffle ? `Zufällig: ${title || "Auswahl"}` : `Spielt: ${title || "Auswahl"}`);
      if (!(this._attrs.speakers || []).length) this._toast("Kein Lautsprecher aktiv – oben links Lautsprecher wählen.", true);
    });
  }
}

const CSS = `
:host { --sf-bg:#f4f8fc; --ink:#283443; --ink2:#445265; --muted:#697789; --sf-hi:#ffffff; --sf-lo:#d4dce4; --sf-lo2:var(--sf-lo2); --acc:#1e9e55;
  transition:--sf-bg .9s ease,--sf-hi .9s ease,--sf-lo .9s ease,--sf-lo2 .9s ease;
  --raise:-4px -4px 9px var(--sf-hi),4px 4px 9px var(--sf-lo); --raise-l:-6px -6px 14px var(--sf-hi),7px 8px 16px var(--sf-lo2);
  --inset:inset 4px 4px 8px var(--sf-lo),inset -4px -4px 8px var(--sf-hi); display:block; }
* { box-sizing:border-box; }
button { font:inherit; color:inherit; border:0; background:none; cursor:pointer; -webkit-tap-highlight-color:transparent; }
svg { width:22px; height:22px; fill:currentColor; flex:none; }
svg.st { fill:none; stroke:currentColor; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
ha-card.sf { display:block; background:var(--sf-bg); border:0; border-radius:20px; overflow:hidden; color:var(--ink);
  box-shadow:-5px -5px 10px #ffffff, 6px 7px 14px #d2dbe4; }
.surface { border-radius:20px; }
.surface { position:relative; display:grid; grid-template-rows:auto 1fr auto auto auto; gap:10px; padding:12px 16px 14px;
  min-height:420px; height:var(--h); background:var(--sf-bg); }
.surface.loading > :not(.toast), .surface:not(.ready) > :not(.toast) { visibility:hidden; }
.surface.narrow { height:auto; min-height:0; }
.top { display:flex; align-items:center; gap:10px; min-height:40px; z-index:2; }
.top.empty { min-height:0; height:0; overflow:hidden; }
.nb.warn { color:#c2410c; }
.timer-badge { margin-left:auto; display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border-radius:999px;
  box-shadow:var(--inset); font-size:.82rem; font-variant-numeric:tabular-nums; color:var(--ink2); }
.timer-badge svg { width:16px; height:16px; color:var(--acc); }
.timer-badge[hidden] { display:none; }
.hero { min-height:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:12px; }
.flow { position:relative; display:flex; align-items:center; justify-content:center; gap:18px; width:100%; min-height:0; flex:1 1 auto; }
.art { position:relative; height:min(100%,340px); aspect-ratio:1; max-width:78vw; border-radius:22px; overflow:hidden;
  background:var(--sf-bg); box-shadow:var(--inset); display:grid; place-items:center; min-height:120px; }
.art img { width:100%; height:100%; object-fit:cover; display:block; border-radius:22px; }
.art img[hidden] { display:none; }
.art .ph svg { width:56px; height:56px; color:#b9c3cf; }
.art .ph[hidden] { display:none; }
.side { height:min(62%,210px); aspect-ratio:1; border-radius:18px; overflow:hidden; opacity:0; pointer-events:none;
  transition:opacity .3s; padding:0; flex:none; }
.side img { width:100%; height:100%; object-fit:cover; display:block; filter:saturate(.85); }
.side.has { opacity:.42; pointer-events:auto; }
.side.has:hover { opacity:.65; }
.surface:not(.wide) .side { display:none; }
.caption { display:flex; align-items:center; justify-content:center; gap:20px; width:min(100%,880px); min-width:0; padding-bottom:4px; }
.copy { flex:1 1 0; min-width:0; max-width:490px; }
.title { font-size:1.45rem; font-weight:750; letter-spacing:-.01em; color:#1d2a39; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sub { margin-top:2px; font-size:.95rem; font-weight:500; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.actions { display:flex; gap:10px; flex:none; }
.nb { display:inline-flex; align-items:center; justify-content:center; width:48px; height:48px; border-radius:50%;
  background:var(--sf-bg); box-shadow:var(--raise); color:var(--ink); transition:box-shadow .15s,color .15s; }
.nb:active, .nb.on { box-shadow:var(--inset); }
.nb.on { color:var(--acc); }
.nb:disabled { opacity:.45; cursor:default; }
.nb.sm { width:40px; height:40px; } .nb.sm svg { width:20px; height:20px; }
.nb.xs { width:32px; height:32px; } .nb.xs svg { width:18px; height:18px; }
.nb.main { width:76px; height:76px; box-shadow:var(--raise-l); color:#1d2a39; }
.nb.main svg { width:34px; height:34px; }
.nb.main:active { box-shadow:var(--inset); }
.progress { display:grid; grid-template-columns:auto 1fr auto; align-items:center; gap:12px; width:min(100%,860px); justify-self:center; }
.t { font-size:.78rem; font-variant-numeric:tabular-nums; color:var(--muted); min-width:38px; text-align:center; }
.groove { position:relative; height:10px; border-radius:999px; box-shadow:var(--inset); cursor:pointer; touch-action:none; }
.groove .fill { position:absolute; inset:2px auto 2px 2px; width:calc(var(--p,0%) - 4px); min-width:0; border-radius:999px; background:var(--acc); opacity:.85; }
.groove .knob { position:absolute; top:50%; left:var(--p,0%); width:18px; height:18px; margin:-9px 0 0 -9px; border-radius:50%;
  background:var(--sf-bg); box-shadow:-2px -2px 5px var(--sf-hi),2px 3px 6px var(--sf-lo2); }
.transport { display:flex; align-items:center; justify-content:center; gap:14px; flex-wrap:nowrap; padding:4px 0 2px; }
.volume { display:flex; align-items:center; justify-content:center; gap:10px; width:min(100%,560px); justify-self:center; }
.volume input { flex:1; }
.pct { min-width:44px; font-size:.82rem; color:var(--muted); font-variant-numeric:tabular-nums; text-align:right; }
input[type=range] { -webkit-appearance:none; appearance:none; height:10px; border-radius:999px; background:var(--sf-bg); box-shadow:var(--inset);
  background-image:linear-gradient(var(--acc),var(--acc)); background-size:var(--p,0%) 100%; background-repeat:no-repeat; outline:none; }
input[type=range]::-webkit-slider-thumb { -webkit-appearance:none; width:20px; height:20px; border-radius:50%; background:var(--sf-bg);
  box-shadow:-2px -2px 5px var(--sf-hi),2px 3px 6px var(--sf-lo2); cursor:pointer; }
input[type=range]::-moz-range-thumb { width:20px; height:20px; border:0; border-radius:50%; background:var(--sf-bg); box-shadow:-2px -2px 5px var(--sf-hi),2px 3px 6px var(--sf-lo2); }
/* breit: Liedtext links (31 %), Cover + Beschriftung rechts – wie in Fabs HOMEii-Anpassung */
.lyrics-panel { display:none; }
.surface.wide.lyrics-on { grid-template-columns:minmax(260px,31%) minmax(0,1fr); column-gap:18px; }
.surface.wide.lyrics-on > :not(.lyrics-panel):not(.sheet-wrap):not(.toast) { grid-column:2; }
.surface.wide.lyrics-on .lyrics-panel { display:flex; grid-column:1; grid-row:1 / -1; min-height:0; flex-direction:column; }
.lyrics-copy { overflow-y:auto; scrollbar-width:none; height:100%; min-height:0; padding:24px 8px 24px 4px; line-height:1.6;
  font-size:clamp(15px,1.15vw,19px); color:var(--ink);
  -webkit-mask-image:linear-gradient(to bottom,transparent,#000 12%,#000 88%,transparent); mask-image:linear-gradient(to bottom,transparent,#000 12%,#000 88%,transparent); }
.lyrics-copy::-webkit-scrollbar { display:none; }
.lyrics-copy { position:relative; }
.lyric-line { padding:9px 2px 7px; opacity:.4; font-weight:650; transform-origin:0 50%;
  transition:opacity .6s ease,color .6s ease,transform .6s cubic-bezier(.22,.8,.3,1); }
.lyric-line .w { transition:color .35s ease; }
.lyric-line.current .w { color:#7b8a9c; }
.lyric-line.current .w.sung { color:#172b40; }
.ball { position:absolute; left:0; top:0; z-index:2; width:10px; height:10px; border-radius:50%; background:var(--acc);
  box-shadow:0 2px 5px rgba(30,158,85,.35); opacity:0; transition:opacity .2s; pointer-events:none; will-change:transform; }
.ball.on { opacity:1; }
.lyrics-bar { display:flex; justify-content:center; padding:6px 0 2px; }
.lyrics-bar .offset { gap:6px; }
.lyric-line.past { opacity:.55; }
.lyric-line.current { opacity:1; color:#172b40; transform:scale(1.035); }
.lyrics-copy .plain { white-space:pre-line; opacity:.8; }
.lmsg { color:var(--muted); font-size:.9rem; text-align:center; padding:18px 8px; margin:0; }
.lmsg.err { color:#b42318; }
/* schmal */
.surface:not(.wide) .caption { flex-direction:column; gap:12px; text-align:center; padding-bottom:8px; }
.surface:not(.wide) .copy { max-width:100%; width:100%; }
.surface.narrow { padding:12px 12px 14px; }
.surface.narrow .art { height:auto; width:min(76vw,300px); }
.surface.narrow .flow { flex:none; }
.surface.narrow .transport { gap:8px; }
.surface.narrow .transport .nb:not(.main) { width:40px; height:40px; }
.surface.narrow .nb.main { width:64px; height:64px; }
.surface.narrow .title { font-size:1.2rem; }
/* sheets */
.sheet-wrap { position:absolute; inset:0; z-index:20; display:flex; align-items:center; justify-content:center; padding:14px;
  background:color-mix(in srgb,var(--sf-bg) 72%,transparent); backdrop-filter:blur(3px); opacity:0; transition:opacity .18s; }
.sheet-wrap.open { opacity:1; }
.sheet-wrap[hidden] { display:none; }
.sheet { width:min(100%,760px); max-height:100%; overflow:auto; background:var(--sf-bg); border-radius:22px; padding:14px 16px 16px;
  box-shadow:-8px -8px 18px var(--sf-hi),10px 12px 24px var(--sf-lo2); scrollbar-width:thin; }
.sheet.tall { height:100%; display:flex; flex-direction:column; overflow:hidden; }
.sheet.small { width:min(100%,460px); }
.sh-head { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.sh-title { flex:1; display:inline-flex; align-items:center; justify-content:center; gap:8px; font-weight:700; min-width:0; }
.sh-title span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sh-title svg { color:var(--acc); width:20px; height:20px; }
.sh-sub { text-align:center; color:var(--muted); font-size:.85rem; margin:-4px 0 6px; }
.offset { display:inline-flex; align-items:center; gap:6px; font-size:.8rem; color:var(--muted); font-variant-numeric:tabular-nums; }
.lyrics-copy.big { flex:1; text-align:center; font-size:clamp(17px,4.4vw,22px); }
.lyrics-copy.big .lyric-line { padding:12px 2px 8px; }
.hint { color:var(--muted); font-size:.82rem; margin:12px 4px 0; }
.hint.center { text-align:center; }
/* equalizer */
.nb.on { color:var(--acc); }
.eq-wrap { touch-action:none; user-select:none; -webkit-user-select:none; margin:4px 0 2px; }
.eq-svg { display:block; width:100%; height:auto; overflow:visible; cursor:ns-resize; }
.eq-grid { stroke:var(--sf-lo); stroke-width:1; } .eq-grid.zero { stroke:var(--muted); stroke-opacity:.5; stroke-dasharray:4 4; }
.eq-lbl, .eq-hz { fill:var(--muted); font-size:11px; } .eq-hz, .eq-val { text-anchor:middle; }
.eq-val { fill:var(--ink); font-size:12px; font-weight:700; }
.eq-area { fill:url(#sf-eq-fill); }
.eq-curve { fill:none; stroke:var(--acc); stroke-width:3; stroke-linecap:round; }
.eq-knob { fill:var(--acc); stroke:var(--sf-bg); stroke-width:3; filter:drop-shadow(1px 2px 2px rgba(0,0,0,.18)); }
.eq-dot:focus { outline:none; } .eq-dot:focus-visible .eq-knob { stroke:var(--ink); }
.eq-svg.off .eq-curve { stroke:var(--muted); stroke-opacity:.5; } .eq-svg.off .eq-knob { fill:var(--muted); fill-opacity:.6; }
.eq-svg.off .eq-area { opacity:.25; }
.eq-name { text-align:center; font-weight:700; margin:4px 0 10px; color:var(--ink2); }
.eq-presets { justify-content:center; }
.eq-presets .gchip { padding:8px 14px; font-size:.82rem; }
.pills { display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin-top:12px; }
.pill { display:inline-flex; align-items:center; gap:6px; padding:10px 16px; border-radius:999px; box-shadow:var(--raise); font-weight:600; font-size:.9rem; }
.pill:active { box-shadow:var(--inset); }
.pill.off { color:#b42318; } .pill svg { width:18px; height:18px; }
.play-row { display:flex; flex-wrap:wrap; gap:10px; margin:2px 0 10px; }
.play-all { color:var(--acc); }
.gchips { display:flex; flex-wrap:wrap; gap:10px; margin:2px 0 14px; justify-content:center; }
.gchip { display:inline-flex; align-items:center; gap:8px; padding:9px 16px; border-radius:999px; box-shadow:var(--raise); font-weight:600; font-size:.88rem; }
.gchip svg { width:18px; height:18px; }
.gchip.on { box-shadow:var(--inset); color:var(--acc); }
.spk-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:12px; }
.spk-card { border-radius:18px; box-shadow:var(--raise); padding:10px 12px; }
.spk-card.na { opacity:.55; }
.spk-main { width:100%; display:flex; align-items:center; gap:10px; text-align:left; }
.spk-ic { width:40px; height:40px; border-radius:12px; box-shadow:var(--inset); display:grid; place-items:center; color:var(--muted); flex:none; }
.spk-card.on .spk-ic { color:var(--acc); }
.spk-txt { flex:1; min-width:0; display:flex; flex-direction:column; }
.spk-name { font-weight:650; line-height:1.25; overflow-wrap:anywhere; }
.spk-state { font-size:.78rem; color:var(--muted); }
.switch { width:46px; height:26px; border-radius:999px; box-shadow:var(--inset); position:relative; flex:none; }
.switch::after { content:""; position:absolute; top:4px; left:4px; width:18px; height:18px; border-radius:50%; background:var(--sf-bg);
  box-shadow:-2px -2px 4px var(--sf-hi),2px 2px 4px var(--sf-lo2); transition:transform .18s; }
.switch.on::after { transform:translateX(20px); background:var(--acc); }
.spk-btns { display:flex; justify-content:flex-end; margin-top:8px; }
.pill.xs { padding:6px 12px; font-size:.78rem; }
.pill.on { box-shadow:var(--inset); color:var(--acc); }
.pill:disabled { opacity:.45; }
.spk-volrow { display:flex; align-items:center; gap:8px; margin-top:10px; color:var(--muted); }
.spk-volrow svg { width:18px; height:18px; }
.spk-volrow input { flex:1; }
.spk-pct { min-width:38px; text-align:right; font-size:.78rem; font-variant-numeric:tabular-nums; }
.lib { display:flex; flex-direction:column; height:100%; min-height:0; }
.lib-body { flex:1; min-height:0; overflow-y:auto; padding:4px 4px 10px; scrollbar-width:thin; }
.tabs { display:flex; gap:6px; padding:8px; margin-top:8px; border-radius:18px; box-shadow:var(--inset); overflow-x:auto; scrollbar-width:none; }
.tab { flex:1 0 auto; display:inline-flex; align-items:center; justify-content:center; gap:6px; padding:9px 12px; border-radius:14px;
  font-size:.82rem; font-weight:600; color:var(--muted); white-space:nowrap; }
.tab svg { width:18px; height:18px; }
.tab.on { background:var(--sf-bg); box-shadow:var(--raise); color:var(--acc); }
.sheet:not(.wide-tabs) .tab span { display:inline; }
.surface.narrow .tab span { display:none; }
.search { display:flex; gap:10px; margin:0 0 10px; }
.saved-badge { display:inline-flex; color:var(--acc); padding:0 6px; }
.saved-badge svg { width:18px; height:18px; }
.lib-body.grid .saved-badge { position:absolute; top:14px; left:14px; background:color-mix(in srgb,var(--sf-bg) 92%,transparent); border-radius:50%; padding:4px; }
.pl-search-in, .search-in { flex:1; min-width:0; padding:11px 16px; border:0; border-radius:999px; background:var(--sf-bg); box-shadow:var(--inset); font:inherit; color:var(--ink); outline:none; }
.grp { margin:14px 4px 6px; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }
.item { position:relative; display:flex; align-items:center; gap:8px; border-radius:16px; }
.item-main { flex:1; min-width:0; display:flex; align-items:center; gap:12px; padding:7px 8px; border-radius:14px; text-align:left; }
.item-main:active { box-shadow:var(--inset); }
.item.current { box-shadow:var(--inset); }
.thumb { width:48px; height:48px; flex:none; border-radius:12px; overflow:hidden; box-shadow:var(--raise); display:grid; place-items:center; color:var(--muted); }
.thumb.round { border-radius:50%; }
.thumb img { width:100%; height:100%; object-fit:cover; display:block; }
.item-txt { min-width:0; display:flex; flex-direction:column; }
.item-t { font-weight:600; font-size:.92rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.item-s { font-size:.78rem; color:var(--muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.lib-body.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(132px,1fr)); gap:14px; align-content:start; }
.lib-body.grid .grp, .lib-body.grid .lmsg, .lib-body.grid .more-btn, .lib-body.grid .play-row { grid-column:1 / -1; }
.lib-body.grid .item { flex-direction:column; padding:10px; box-shadow:var(--raise); border-radius:18px; }
.lib-body.grid .item-main { flex-direction:column; text-align:center; padding:0; width:100%; }
.lib-body.grid .thumb { width:100%; height:auto; aspect-ratio:1; border-radius:14px; }
.lib-body.grid .thumb svg { width:40%; height:40%; }
.lib-body.grid .thumb.round { border-radius:50%; }
.lib-body.grid .item-txt { width:100%; }
.lib-body.grid .item-t { white-space:normal; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.lib-body.grid .dots { position:absolute; top:14px; right:14px; background:color-mix(in srgb,var(--sf-bg) 92%,transparent); }
.more-btn { display:block; margin:12px auto 4px; padding:10px 22px; border-radius:999px; box-shadow:var(--raise); font-weight:600; font-size:.88rem; }
.menu { position:absolute; right:6px; top:calc(100% - 6px); z-index:5; min-width:200px; padding:6px; border-radius:16px; background:var(--sf-bg);
  box-shadow:-6px -6px 14px var(--sf-hi),8px 10px 20px var(--sf-lo2); display:flex; flex-direction:column; }
.menu button { display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:12px; font-size:.9rem; text-align:left; }
.menu button:active { box-shadow:var(--inset); }
.menu svg { width:18px; height:18px; color:var(--acc); }
.toast { position:absolute; left:50%; bottom:16px; z-index:30; transform:translate(-50%,20px); max-width:calc(100% - 32px);
  padding:10px 18px; border-radius:999px; background:var(--sf-bg); box-shadow:-5px -5px 12px var(--sf-hi),6px 8px 16px var(--sf-lo2);
  font-size:.86rem; font-weight:600; opacity:0; pointer-events:none; transition:opacity .2s,transform .2s; text-align:center; }
.toast.show { opacity:1; transform:translate(-50%,0); }
.toast.err { color:#b42318; }
.surface.unavailable .transport, .surface.unavailable .volume { opacity:.5; pointer-events:none; }
`;

if (!customElements.get("spotify-flex-flow-card")) customElements.define("spotify-flex-flow-card", SpotifyFlexFlowCard);
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "spotify-flex-flow-card")) {
  window.customCards.push({ type: "spotify-flex-flow-card", name: "Spotify Flex Flow", description: "Player im HOMEii-Aufbau für Spotify Flex", preview: false });
}
console.info(`%c SPOTIFY-FLEX-FLOW %c ${CARD_VERSION} `, "background:#1e9e55;color:#fff;border-radius:4px 0 0 4px;padding:2px 4px", "background:#f4f8fc;color:#283443;border-radius:0 4px 4px 0;padding:2px 4px");
