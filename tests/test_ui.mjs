// UI smoke test: loads index.html + app.js in happy-dom with a mocked backend.
import { Window } from "happy-dom";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";

const base = new URL("../spotify_flex/rootfs/opt/flex/static/", import.meta.url);
const win = new Window({ url: "http://ha.local/api/hassio_ingress/TOKEN/" });
const html = readFileSync(new URL("index.html", base), "utf8").replace(/<script[^>]*><\/script>/, "");
win.document.write(html);
const calls = [];
const state = {
  version: "1.0.0",
  receiver: { running: true, logged_in: false, auth_code: { url: "https://spotify.com/pair?code=ABCD", code: "ABCD-EFGH", expires_at: new Date(Date.now() + 600000).toISOString() } },
  web: { configured: true, connected: true, redirect_uri: "http://127.0.0.1:8765/callback" },
  player: { online: true, playing: true, volume: 60, repeat: "off", track: { uri: "spotify:track:T1", name: "Closer <b>", artists: "NIN", duration_ms: 300000, position_ms: 1000 } },
  speakers: [{ id: "111", name: "HomePod Links", selected: false, volume: 40 }],
};
const pages = {
  playlists: { node: "playlists", title: "Playlists", items: [{ id: "P1", node: "playlist:P1", uri: "spotify:playlist:P1", type: "playlist", name: "Fabian", subtitle: "Fab242 · 69 Titel", playable: true, expandable: true }], next_offset: null },
  "playlist:P1": { node: "playlist:P1", title: "Fabian", context_uri: "spotify:playlist:P1", playlist: { id: "P1", name: "Fabian", editable: true }, items: [{ id: "T2", uri: "spotify:track:T2", type: "track", name: "Euphoria", subtitle: "Delerium", playable: true, duration_ms: 328000, context_uri: "spotify:playlist:P1" }], next_offset: 50, total: 69 },
};
win.fetch = async (url, opts = {}) => {
  const u = new URL(url, win.location.href);
  calls.push([opts.method || "GET", u.pathname, opts.body]);
  let body = {};
  if (u.pathname.endsWith("/api/state")) body = state;
  else if (u.pathname.endsWith("/api/browse")) body = pages[u.searchParams.get("node")];
  else if (u.pathname.endsWith("/api/play")) body = { ok: true, warning: null };
  else if (u.pathname.endsWith("/api/now/liked")) body = { liked: true };
  else if (u.pathname.includes("/api/speakers/")) { state.speakers[0].selected = true; body = { speakers: state.speakers }; }
  return { ok: true, status: 200, json: async () => body };
};
win.WebSocket = class { constructor() { setTimeout(() => {}, 0); } };
win.eval(readFileSync(new URL("app.js", base), "utf8"));
const tick = () => new Promise((r) => setTimeout(r, 50));
await tick(); await tick();
const d = win.document;
assert.match(d.querySelector("#setup").textContent, /ABCD-EFGH/, "pairing code shown");
assert.match(d.querySelector("#now").innerHTML, /Closer &lt;b&gt;/, "escaped title");
assert.match(d.querySelector("#browser").textContent, /Fabian/);
assert.ok(calls.some(([m, p]) => p.endsWith("/api/hassio_ingress/TOKEN/api/state")), "relative ingress path");
d.querySelector("#browser .row[data-i]").click(); await tick();
assert.match(d.querySelector("#browser").textContent, /Euphoria/);
assert.ok(d.querySelector('[data-act="edit-playlist"]'), "edit button for own playlist");
d.querySelector("#browser .row[data-i]").click(); await tick();
const play = calls.find(([, p]) => p.endsWith("/api/play"));
assert.deepEqual(JSON.parse(play[2]), { uri: "spotify:track:T2", context_uri: "spotify:playlist:P1" });
d.querySelector('#speakers [data-act="toggle"]').click(); await tick();
assert.equal(d.querySelector('#speakers [data-act="toggle"]').getAttribute("aria-checked"), "true");
d.querySelector('#browser [data-act="menu"]').click(); await tick();
assert.ok(!d.querySelector("#sheet").hidden && /Zu Playlist hinzufügen/.test(d.querySelector("#sheet").textContent));
console.log("ui smoke test OK");
await win.happyDOM.close();
process.exit(0);
