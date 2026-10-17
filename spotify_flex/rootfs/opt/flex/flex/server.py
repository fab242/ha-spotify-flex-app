"""Spotify Flex app: HTTP/WebSocket backend behind Home Assistant ingress."""
from __future__ import annotations

import asyncio
import json
import secrets
import logging
import statistics
import subprocess
import time
from collections import deque
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web
import aiohttp

from .api import SpotifyAuthError, SpotifyClient, SpotifyError, valid_id
from .browse import browse
from .const import INGRESS_PORT, LIBRESPOT_STATE, OPTIONS_FILE, REDIRECT_URI, VERSION
from .oauth import WebAuth
from . import appopts, hassbridge, netheal
from .groups import GroupStore
from .speakercfg import SpeakerConfig
from .eq import Equalizer, EqError
from .announce import Announcer, MediaPrep
from .lyricsync import AlignerClient, Lyrics, LyricSync
from .receiver import Librespot, MetaPipe, OwnTone

logging.basicConfig(level=logging.INFO, format="[spotify-flex] %(levelname)s %(message)s")
_LOGGER = logging.getLogger("flex")

STATIC = Path(__file__).resolve().parent.parent / "static"
LATENCY_FILE = Path("/data/audio_latency.json")
INGRESS_PEER = "172.30.32.2"  # Supervisor ingress proxy (the app UI)
LOCAL_PEERS = {"127.0.0.1", "::1"}  # Home Assistant core (host network) - needs the API token


def load_options() -> dict:
    try:
        return json.loads(Path(OPTIONS_FILE).read_text())
    except (OSError, ValueError):
        return {}


def error_response(err: Exception) -> web.Response:
    status = getattr(err, "status", None) or 500
    if isinstance(err, SpotifyAuthError):
        status = 401
    if status < 400 or status > 599:
        status = 502
    return web.json_response({"error": str(err), "status": status}, status=status)


class App:
    def __init__(self) -> None:
        self.options = load_options()
        self.session: aiohttp.ClientSession | None = None
        self.receiver: Librespot | None = None
        self.owntone: OwnTone | None = None
        self.announcer: Announcer | None = None
        self.auth: WebAuth | None = None
        self.api: SpotifyClient | None = None
        self.status: dict | None = None
        self.sockets: set[web.WebSocketResponse] = set()
        self.stop = asyncio.Event()
        self.tasks: list[asyncio.Task] = []
        self.auth_pending: dict | None = None  # device-code login in progress
        self.groups = GroupStore()
        self.speaker_cfg = SpeakerConfig()
        self.eq = Equalizer()
        self.token = hassbridge.api_token()
        self.integration = "unknown"
        # audible position: Spotify position minus the measured audio delay (pipe + OwnTone + AirPlay)
        self.meta = MetaPipe("/music/spotify.metadata")
        self.status_at = 0.0
        self.sync_track: str | None = None
        self.sync_since = 0.0
        self.sync_wake: asyncio.Event | None = None
        self.latency = deque(maxlen=15)
        try:
            saved = json.loads(LATENCY_FILE.read_text()).get("latency_ms")
            if isinstance(saved, (int, float)) and 0 <= saved <= 12000:
                self.latency.append(float(saved))
        except (OSError, ValueError):
            pass

    # ------------------------------------------------------------ lifecycle
    async def start(self, _app: web.Application) -> None:
        self.session = aiohttp.ClientSession()
        self.receiver = Librespot(self.session)
        self.owntone = OwnTone(self.session)
        self.media = MediaPrep(self.session, f"http://127.0.0.1:{INGRESS_PORT}")
        self.announcer = Announcer(self.owntone, self.pause_for_announcement, self.activate_group, self.media)
        self.auth = WebAuth(self.session, self.options.get("client_id", ""))
        self.api = SpotifyClient(self.session, self.auth.token)
        url = str(self.options.get("lyrics_aligner_url") or "").strip()
        self.lyricsync = LyricSync(self.session, Lyrics(self.session, VERSION),
                                   AlignerClient(self.session, url, str(self.options.get("lyrics_aligner_token") or "")) if url else None,
                                   lambda: (self.status, self.status_at))
        self.lyricsync.start()
        self.tasks = [
            asyncio.create_task(self.receiver.events(self.on_event, self.stop)),
            asyncio.create_task(self.poll_status()),
            asyncio.create_task(self.heal_loop()),
            asyncio.create_task(self.bridge()),
            asyncio.create_task(self.audio_sync_loop()),
        ]

    async def bridge(self) -> None:
        """Install/refresh the bundled HA integration and announce the app via discovery."""
        if self.options.get("ha_integration", True) is False:
            self.integration = "disabled"
            return
        try:
            self.integration = await asyncio.get_running_loop().run_in_executor(
                None, hassbridge.install_integration)
        except OSError as err:
            self.integration = "error"
            _LOGGER.warning("integration install failed: %s", err)
            return
        _LOGGER.info("HA integration: %s", self.integration)
        if self.integration in ("installed", "updated"):
            await hassbridge.notify(
                self.session, "Spotify Flex",
                "Die Home-Assistant-Integration „Spotify Flex Player“ wurde "
                + ("installiert" if self.integration == "installed" else "aktualisiert")
                + ". Bitte Home Assistant einmal neu starten – danach erscheint sie unter "
                "Einstellungen → Geräte & Dienste als „Entdeckt“.")
        await asyncio.sleep(5)
        await hassbridge.push_discovery(self.session, self.token)

    async def heal_loop(self) -> None:
        """Re-check unreachable Spotify servers every 30 minutes (first run is at boot)."""
        while not self.stop.is_set():
            await asyncio.sleep(1800)
            try:
                report = await asyncio.get_running_loop().run_in_executor(None, netheal.heal)
                if report.get("overrides"):
                    _LOGGER.info("netheal overrides: %s", report["overrides"])
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("netheal failed: %s", err)

    async def shutdown(self, _app: web.Application) -> None:
        self.stop.set()
        if getattr(self, "lyricsync", None):
            await self.lyricsync.stop()
        for t in self.tasks:
            t.cancel()
        for ws in list(self.sockets):
            await ws.close()
        if self.session:
            await self.session.close()

    async def poll_status(self) -> None:
        """Keep a fresh status even without events (position, login state)."""
        while not self.stop.is_set():
            try:
                await self.refresh_status(broadcast=True)
            except Exception:  # noqa: BLE001 - never let the poller die
                pass
            await asyncio.sleep(10)

    async def refresh_status(self, broadcast: bool = False) -> dict:
        try:
            self.auth_pending = await self.receiver.auth_code()
        except SpotifyError:
            self.auth_pending = None
        if self.auth_pending:
            self.status = None  # /status would block until the login is done
        else:
            try:
                self.status = await self.receiver.status()
                self.status_at = time.time()
            except SpotifyError:
                self.status = None
        if broadcast:
            await self.broadcast({"type": "status", "data": self.player_view()})
        return self.status or {}

    # ------------------------------------------------- audible position sync
    async def audio_sync_loop(self) -> None:
        """Every 3 s (and right after track changes/seeks) tell OwnTone the Spotify position of
        the audio it reads, then measure how far the audible position lags behind."""
        self.sync_wake = asyncio.Event()
        while not self.stop.is_set():
            woke = False
            try:
                await asyncio.wait_for(self.sync_wake.wait(), timeout=3)
                woke = True
            except asyncio.TimeoutError:
                pass
            self.sync_wake.clear()
            if woke:
                await asyncio.sleep(0.3)  # let the new audio reach the pipe
            try:
                await self.audio_sync()
            except Exception as err:  # noqa: BLE001 - keep the loop alive
                _LOGGER.debug("audio sync: %s", err)

    async def audio_sync(self) -> None:
        announcer = getattr(self, "announcer", None)
        if self.auth_pending or (announcer and announcer.active):
            return
        try:
            st = await self.receiver.status()
        except SpotifyError:
            return
        if not st:
            return
        self.status, self.status_at = st, time.time()
        track = st.get("track") or {}
        uri, pos, dur = track.get("uri"), track.get("position"), track.get("duration")
        if st.get("stopped") or st.get("paused") or not uri or pos is None:
            return
        if uri != self.sync_track:
            self.sync_track, self.sync_since = uri, time.time()
        self.meta.send(MetaPipe.progress_item(int(pos), dur))
        if time.time() - self.sync_since < 9:  # our marks for this track are not audible yet
            return
        try:
            pl = await self.owntone.player()
        except SpotifyError:
            return
        prog = pl.get("item_progress_ms")
        if pl.get("state") != "play" or not isinstance(prog, (int, float)) or prog <= 0:
            return
        lat = pos + (time.time() - self.status_at) * 1000 - prog
        if 0 <= lat <= 12000:
            self.latency.append(lat)
            if len(self.latency) % 5 == 0:
                try:
                    LATENCY_FILE.write_text(json.dumps({"latency_ms": round(self.latency_ms())}))
                except OSError:
                    pass

    async def speakers(self, include_hidden: bool = False) -> list[dict]:
        """OwnTone outputs with the user's names and settings (hidden ones left out)."""
        return self.speaker_cfg.apply(await self.owntone.outputs(), include_hidden)

    async def select_outputs(self, ids: list[str]) -> None:
        """Select exactly these outputs; newly switched-on ones get their start volume."""
        before = {s["id"] for s in await self.owntone.outputs() if s["selected"]}
        await self.owntone.set_outputs(ids)
        for oid in ids:
            start = self.speaker_cfg.get(oid)["start_volume"]
            if oid not in before and start is not None:
                try:
                    await self.owntone.set_output(oid, volume=start)
                except SpotifyError:
                    pass

    async def pause_for_announcement(self) -> None:
        try:
            st = await self.receiver.status()
            if st and not st.get("paused") and not st.get("stopped"):
                await self.receiver.pause()
        except SpotifyError:
            pass

    async def activate_group(self, name_or_id: str) -> dict:
        """Gruppe (Name oder ID) aktivieren: genau ihre erreichbaren Lautsprecher einschalten."""
        key = str(name_or_id).strip().lower()
        group = next((g for g in self.groups.all() if g["id"] == name_or_id or g["name"].lower() == key), None)
        if not group:
            raise SpotifyError(f"Gruppe „{name_or_id}“ gibt es nicht.", 404)
        known = {s["id"] for s in await self.speakers(True)}
        ids = [i for i in group["speakers"] if i in known]
        if not ids:
            raise SpotifyError(f"Kein Lautsprecher der Gruppe „{group['name']}“ ist gerade erreichbar.", 409)
        await self.select_outputs(ids)
        return group

    def latency_ms(self) -> float | None:
        return statistics.median(self.latency) if self.latency else None

    async def on_event(self, event: dict) -> None:
        kind = event.get("type")
        if kind in ("metadata", "playing", "seek", "will_play", "active") and self.sync_wake:
            self.sync_wake.set()
        if kind in ("metadata", "playing", "paused", "stopped", "not_playing", "seek", "volume",
                    "shuffle_context", "repeat_context", "repeat_track", "active", "inactive",
                    "receiver_connected", "will_play"):
            await self.refresh_status()
            await self.broadcast({"type": "status", "data": self.player_view(), "event": kind})

    async def broadcast(self, message: dict) -> None:
        dead = []
        for ws in self.sockets:
            try:
                await ws.send_json(message)
            except (ConnectionError, RuntimeError):
                dead.append(ws)
        for ws in dead:
            self.sockets.discard(ws)

    # -------------------------------------------------------------- views
    def heard_position(self, pos: int | None) -> int | None:
        """Track position that is audible right now (may be negative right after a track
        change: the previous track is still playing from the buffers)."""
        if pos is None:
            return None
        lat = self.latency_ms()
        return round(pos - lat) if lat is not None else pos

    def player_view(self) -> dict:
        s = self.status or {}
        track = s.get("track") or None
        if track:
            track = {
                "uri": track.get("uri"),
                "name": track.get("name"),
                "artists": ", ".join(track.get("artist_names") or []),
                "album": track.get("album_name"),
                "image": track.get("album_cover_url"),
                "position_ms": self.heard_position(track.get("position")),
                "position_at": round(self.status_at * 1000) if self.status_at else None,
                "spotify_position_ms": track.get("position"),
                "latency_ms": round(self.latency_ms()) if self.latency_ms() is not None else None,
                "duration_ms": track.get("duration"),
                "format": track.get("format"),
            }
        steps = s.get("volume_steps") or 100
        return {
            "online": self.status is not None,
            "username": s.get("username"),
            "device_id": s.get("device_id"),
            "device_name": s.get("device_name") or self.options.get("device_name"),
            "playing": bool(s) and not s.get("stopped", True) and not s.get("paused", True),
            "paused": bool(s.get("paused")),
            "stopped": s.get("stopped", True) if s else True,
            "buffering": bool(s.get("buffering")),
            "volume": round(100 * (s.get("volume") or 0) / steps) if s else None,
            "shuffle": bool(s.get("shuffle_context")),
            "repeat": "track" if s.get("repeat_track") else "context" if s.get("repeat_context") else "off",
            "context_uri": s.get("context_uri"),
            "track": track,
        }

    async def state(self) -> dict:
        await self.refresh_status()
        auth_code = self.auth_pending
        receiver_ok, logged_in = bool(auth_code), False
        if not auth_code:
            try:
                root = await self.receiver.root()
                receiver_ok = True
                logged_in = bool(root.get("playback_ready")) if isinstance(root, dict) else False
            except SpotifyError:
                pass
        speakers, speaker_error = [], None
        try:
            speakers = await self.speakers()
        except SpotifyError as err:
            speaker_error = str(err)
        groups = self.groups.all()
        return {
            "version": VERSION,
            "receiver": {"running": receiver_ok, "logged_in": logged_in or bool(self.status),
                         "auth_code": auth_code},
            "web": {"configured": self.auth.configured, "connected": self.auth.connected,
                    "redirect_uri": REDIRECT_URI},
            "player": self.player_view(),
            "speakers": speakers,
            "speaker_error": speaker_error,
            "groups": groups,
            "active_group": GroupStore.active(groups, speakers),
            "network": self.network_report(),
            "integration": self.integration,
            "announcement": self.announcer.state() if self.announcer else {"active": False, "current": None},
            "lyrics_analysis": self.lyricsync.health() if getattr(self, "lyricsync", None) else {"configured": False},
        }

    @staticmethod
    def network_report() -> dict | None:
        try:
            return json.loads(netheal.REPORT_FILE.read_text())
        except (OSError, ValueError):
            return None

    def user_id(self) -> str:
        return (self.status or {}).get("username") or ""


# ---------------------------------------------------------------- web layer
def build_app() -> web.Application:
    flex = App()

    @web.middleware
    async def guard(request: web.Request, handler):
        peer = request.remote or ""
        if peer in LOCAL_PEERS and request.path.startswith("/announce-media/"):
            pass  # OwnTone holt vorbereitete Durchsagen (zufällige Namen, nur lokal) ohne Token
        elif peer in LOCAL_PEERS:
            auth = request.headers.get("Authorization", "")
            given = auth[7:] if auth.startswith("Bearer ") else request.query.get("token", "")
            if not secrets.compare_digest(given.encode(), flex.token.encode()):
                return web.Response(status=401, text="API-Token fehlt oder ist falsch.")
        elif peer != INGRESS_PEER:
            return web.Response(status=403, text="Nur über Home Assistant erreichbar.")
        try:
            return await handler(request)
        except SpotifyError as err:
            return error_response(err)
        except (ValueError, KeyError, TypeError) as err:
            return web.json_response({"error": f"Ungültige Anfrage: {err}", "status": 400}, status=400)

    app = web.Application(middlewares=[guard], client_max_size=4 * 1024 * 1024)
    app.on_startup.append(flex.start)
    app.on_cleanup.append(flex.shutdown)
    r = web.RouteTableDef()

    async def body(request: web.Request) -> dict:
        if not request.can_read_body:
            return {}
        data = await request.json()
        if not isinstance(data, dict):
            raise ValueError("JSON-Objekt erwartet")
        return data

    def ok(data: Any = None) -> web.Response:
        return web.json_response(data if data is not None else {"ok": True})

    # ---- vorbereitete Durchsagen für OwnTone
    @r.get("/announce-media/{name}")
    async def announce_media(request):
        path = flex.media.path(request.match_info["name"]) if getattr(flex, "media", None) else None
        if not path:
            raise web.HTTPNotFound()
        return web.FileResponse(path, headers={"Cache-Control": "no-store"})

    # ---- static UI
    @r.get("/")
    async def index(_request):
        # version in the asset URLs: after an update the browser must not keep old CSS/JS
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        html = html.replace('static/style.css"', f'static/style.css?v={VERSION}"') \
                   .replace('static/app.js"', f'static/app.js?v={VERSION}"')
        return web.Response(text=html, content_type="text/html", headers={"Cache-Control": "no-store"})

    @r.get("/static/{name}")
    async def static_file(request):
        name = request.match_info["name"]
        path = (STATIC / name).resolve()
        if path.parent != STATIC.resolve() or not path.is_file():
            raise web.HTTPNotFound()
        resp = web.FileResponse(path)
        resp.headers["Cache-Control"] = "no-cache"
        return resp

    # ---- live updates
    @r.get("/ws")
    async def websocket(request):
        ws = web.WebSocketResponse(heartbeat=25)
        await ws.prepare(request)
        flex.sockets.add(ws)
        await ws.send_json({"type": "status", "data": flex.player_view()})
        try:
            async for msg in ws:
                if msg.type == WSMsgType.ERROR:
                    break
        finally:
            flex.sockets.discard(ws)
        return ws

    # ---- setup / state
    @r.get("/api/state")
    async def get_state(_request):
        return ok(await flex.state())

    @r.get("/api/ha/token")
    async def ha_token(request):
        if request.remote != INGRESS_PEER:  # only shown inside the app UI
            raise web.HTTPForbidden(text="Nur in der App sichtbar.")
        return ok({"token": flex.token, "port": INGRESS_PORT})

    @r.post("/api/web/authorize")
    async def web_authorize(_request):
        return ok({"url": flex.auth.authorize_url(), "redirect_uri": REDIRECT_URI})

    @r.post("/api/web/finish")
    async def web_finish(request):
        data = await body(request)
        await flex.auth.finish(str(data.get("url", "")))
        flex.api.clear_cache()
        profile = await flex.api.profile()
        return ok({"connected": True, "name": profile.get("display_name") or profile.get("id")})

    @r.post("/api/web/logout")
    async def web_logout(_request):
        flex.auth.logout()
        flex.api.clear_cache()
        return ok()

    @r.post("/api/receiver/logout")
    async def receiver_logout(_request):
        path = Path(LIBRESPOT_STATE)
        try:
            state = json.loads(path.read_text())
            state["credentials"] = {}
            path.write_text(json.dumps(state))
        except (OSError, ValueError):
            pass
        subprocess.run(["s6-svc", "-r", "/run/service/svc-golibrespot"], check=False, timeout=10)
        return ok()

    # ---- library (Web API)
    @r.get("/api/browse")
    async def api_browse(request):
        node = request.query.get("node", "root")
        offset = int(request.query.get("offset", 0) or 0)
        uid = flex.user_id() or (await flex.api.profile()).get("id", "")
        return ok(await browse(flex.api, uid, node, offset))

    @r.get("/api/search")
    async def api_search(request):
        q = request.query.get("q", "")
        types = [t for t in request.query.get("types", "track,album,artist,playlist").split(",") if t]
        result = await flex.api.search(q, types)
        for page in result.values():
            for item in page["items"]:
                if item["expandable"] and item.get("id"):
                    item["node"] = f"{item['type']}:{item['id']}"
        return ok(result)

    @r.post("/api/library")
    async def api_library(request):
        data = await body(request)
        uris = [str(u) for u in data.get("uris") or []]
        action = data.get("action")
        if action == "contains":
            return ok({"contains": await flex.api.library_contains(uris)})
        if action == "save":
            await flex.api.library_save(uris)
        elif action == "remove":
            await flex.api.library_remove(uris)
        else:
            raise ValueError("action muss save, remove oder contains sein")
        flex.api.clear_cache()  # gespeicherte Playlists/Titel sofort in der Bibliothek zeigen
        return ok()

    @r.post("/api/playlists")
    async def api_playlist_create(request):
        data = await body(request)
        return ok(await flex.api.create_playlist(str(data.get("name", "")).strip(),
                                                 str(data.get("description", "")), bool(data.get("public"))))

    @r.put("/api/playlists/{pid}")
    async def api_playlist_update(request):
        data = await body(request)
        await flex.api.update_playlist(valid_id(request.match_info["pid"]), name=data.get("name"),
                                       description=data.get("description"), public=data.get("public"))
        return ok()

    @r.post("/api/playlists/{pid}/items")
    async def api_playlist_add(request):
        data = await body(request)
        return ok(await flex.api.playlist_add(request.match_info["pid"], [str(u) for u in data.get("uris") or []],
                                              data.get("position")))

    @r.delete("/api/playlists/{pid}/items")
    async def api_playlist_remove(request):
        data = await body(request)
        return ok(await flex.api.playlist_remove(request.match_info["pid"], [str(u) for u in data.get("uris") or []],
                                                 data.get("snapshot_id")))

    @r.post("/api/playlists/{pid}/reorder")
    async def api_playlist_reorder(request):
        data = await body(request)
        return ok(await flex.api.reorder_playlist(request.match_info["pid"], int(data["range_start"]),
                                                  int(data["insert_before"]), int(data.get("range_length", 1)),
                                                  data.get("snapshot_id")))

    @r.get("/api/queue")
    async def api_queue(_request):
        return ok(await flex.api.queue())

    @r.post("/api/request")
    async def api_request(request):
        data = await body(request)
        result = await flex.api.request(str(data.get("method", "GET")), str(data.get("path", "")),
                                        params=data.get("params") or None, body=data.get("body"))
        return ok({"data": result})

    # ---- playback (local receiver, no Web API quota needed)
    @r.post("/api/play")
    async def api_play(request):
        data = await body(request)
        uri = str(data.get("uri", ""))
        context = data.get("context_uri") or None
        try:  # Startposition (z. B. Podcast weiterhören), in ms
            position = max(0, int(data.get("position_ms") or 0)) or None
        except (TypeError, ValueError):
            position = None
        if uri == "liked":
            uri = f"spotify:user:{flex.user_id()}:collection"
        if context and context != uri:
            await flex.receiver.play(context, skip_to_uri=uri, position=position)
        else:
            await flex.receiver.play(uri, position=position)
        if flex.sync_wake:
            flex.sync_wake.set()
        warning = None
        try:
            if not any(o["selected"] for o in await flex.speakers()):
                warning = "Es ist kein Lautsprecher ausgewählt – bitte unter „Lautsprecher“ einen aktivieren."
        except SpotifyError:
            warning = "Lautsprecher-Dienst (OwnTone) antwortet gerade nicht."
        return ok({"ok": True, "warning": warning})

    @r.post("/api/player/{action}")
    async def api_player(request):
        action = request.match_info["action"]
        data = await body(request)
        rec = flex.receiver
        if action == "playpause":
            await rec.playpause()
        elif action == "pause":
            await rec.pause()
        elif action == "resume":
            await rec.resume()
        elif action == "next":
            await rec.next()
        elif action == "prev":
            await rec.prev()
        elif action == "seek":
            await rec.seek(int(data["position_ms"]))
        elif action == "volume":
            await rec.volume(int(data["percent"]))
        elif action == "shuffle":
            await rec.shuffle(bool(data.get("on")))
        elif action == "repeat":
            await rec.repeat(str(data.get("mode", "off")))
        elif action == "queue":
            await rec.add_to_queue(str(data["uri"]))
        else:
            raise web.HTTPNotFound(text="Unbekannte Aktion")
        if action in ("next", "prev", "seek", "resume", "playpause") and flex.sync_wake:
            flex.sync_wake.set()
        status = await flex.refresh_status(broadcast=True)
        return ok({"player": flex.player_view(), "raw": bool(status)})

    # ---- speakers (OwnTone outputs)
    @r.get("/api/speakers")
    async def api_speakers(_request):
        return ok({"speakers": await flex.speakers()})

    @r.post("/api/speakers/{oid}")
    async def api_speaker_set(request):
        data = await body(request)
        oid = request.match_info["oid"]
        volume = flex.speaker_cfg.clamp(oid, data.get("volume"))
        if data.get("selected") and volume is None:
            volume = flex.speaker_cfg.get(oid)["start_volume"]
        try:
            await flex.owntone.set_output(oid, selected=data.get("selected"), volume=volume, pin=data.get("pin"))
        except SpotifyError as err:
            if err.status == 400 and data.get("selected"):
                oid = request.match_info["oid"]
                spk = next((s for s in await flex.speakers(True) if s["id"] == oid), None)
                if spk and spk["needs_pin"] and not data.get("pin"):
                    raise SpotifyError(f"{spk['name']} zeigt jetzt eine PIN an – bitte erneut einschalten "
                                       "und die PIN eingeben.", 409) from err
                raise SpotifyError(
                    f"{spk['name'] if spk else 'Der Lautsprecher'} konnte nicht verbunden werden. "
                    "Details stehen im Protokoll der App (Einstellungen → Apps → Spotify Flex → Protokoll).",
                    409) from err
            raise
        return ok(await speakers_changed())

    async def speakers_changed() -> dict:
        speakers = await flex.speakers()
        groups = flex.groups.all()
        data = {"speakers": speakers, "groups": groups, "active_group": GroupStore.active(groups, speakers)}
        await flex.broadcast({"type": "speakers", "data": data})
        return data

    @r.post("/api/speakers")
    async def api_speakers_set(request):
        """Select exactly the given speakers ({"speakers": [ids]}), others are switched off."""
        data = await body(request)
        await flex.select_outputs([str(i) for i in data.get("speakers") or []])
        return ok(await speakers_changed())

    # ---- speaker settings (configuration page)
    @r.get("/api/config/speakers")
    async def api_cfg_speakers(_request):
        return ok({"speakers": await flex.speakers(True), "groups": flex.groups.all()})

    @r.put("/api/config/speakers/{oid}")
    async def api_cfg_speaker_set(request):
        data = await body(request)
        oid = request.match_info["oid"]
        if oid not in {s["id"] for s in await flex.owntone.outputs()}:
            raise SpotifyError("Lautsprecher nicht gefunden.", 404)
        flex.speaker_cfg.set(oid, data)
        result = await speakers_changed()
        return ok(dict(result, all=await flex.speakers(True)))

    # ---- equalizer (applied live by flex-eq)
    @r.get("/api/config/eq")
    async def api_cfg_eq(_request):
        return ok(flex.eq.view())

    @r.put("/api/config/eq")
    async def api_cfg_eq_set(request):
        data = await body(request)
        try:
            return ok(flex.eq.update(data))
        except EqError as err:
            raise SpotifyError(str(err), 400) from err

    # ---- receiver settings (device name, quality, normalisation)
    @r.get("/api/config/app")
    async def api_cfg_app(_request):
        return ok({"settings": appopts.receiver_settings(flex.options), "bitrates": list(appopts.BITRATES)})

    @r.put("/api/config/app")
    async def api_cfg_app_set(request):
        data = await body(request)
        try:
            flex.options, restarted = await appopts.apply(flex.session, flex.options, data)
        except appopts.OptionsError as err:
            raise SpotifyError(str(err), 400) from err
        return ok({"settings": appopts.receiver_settings(flex.options), "restarted": restarted})

    @r.post("/api/config/speakers/{oid}/pair")
    async def api_cfg_speaker_pair(request):
        """Pair a device that asks for a PIN (e.g. Apple TV). Without pin: make it show one."""
        data = await body(request)
        oid = request.match_info["oid"]
        before = next((s for s in await flex.owntone.outputs() if s["id"] == oid), None)
        if not before:
            raise SpotifyError("Lautsprecher nicht gefunden.", 404)
        try:
            await flex.owntone.set_output(oid, selected=True, pin=str(data["pin"]) if data.get("pin") else None)
        except SpotifyError as err:
            if not data.get("pin"):
                return ok({"pin_shown": True})
            raise SpotifyError("Die PIN wurde nicht angenommen – bitte neu anfordern und erneut eingeben.", 409) from err
        if not before["selected"]:
            await flex.owntone.set_output(oid, selected=False)
        return ok({"paired": True, "all": await flex.speakers(True)})

    # ---- saved speaker groups
    @r.get("/api/groups")
    async def api_groups(_request):
        speakers = await flex.speakers()
        groups = flex.groups.all()
        return ok({"groups": groups, "active_group": GroupStore.active(groups, speakers)})

    @r.post("/api/groups")
    async def api_group_create(request):
        data = await body(request)
        group = flex.groups.create(str(data.get("name", "")), data.get("speakers") or [])
        result = await speakers_changed()
        return ok(dict(result, group=group))

    @r.put("/api/groups/{gid}")
    async def api_group_update(request):
        data = await body(request)
        flex.groups.update(request.match_info["gid"], name=data.get("name"), speakers=data.get("speakers"))
        return ok(await speakers_changed())

    @r.delete("/api/groups/{gid}")
    async def api_group_delete(request):
        flex.groups.delete(request.match_info["gid"])
        return ok(await speakers_changed())

    # ---- Durchsagen (TTS, Nachrichten, Radio-Links) über die AirPlay-Lautsprecher
    # ---- Liedtexte (lrclib + genaue Wortzeiten aus der Liedtext-Analyse)
    @r.get("/api/lyrics")
    async def api_lyrics(request):
        q = request.query
        uri = q.get("uri", "")
        title, artist, album, dur = q.get("title", ""), q.get("artist", ""), q.get("album") or None, q.get("duration_ms")
        if not uri:  # ohne Angabe: der laufende Titel
            track = (flex.status or {}).get("track") or {}
            uri, title = track.get("uri") or "", track.get("name") or ""
            artist, album, dur = ", ".join(track.get("artist_names") or []), track.get("album_name"), track.get("duration")
        if not uri or not title:
            raise ValueError("Titel fehlt")
        return ok(await flex.lyricsync.for_track(uri, title, artist, album, int(dur) if dur else None))

    @r.post("/api/lyrics/coverage")
    async def api_lyrics_coverage(request):
        data = await body(request)
        return ok(await flex.lyricsync.coverage([str(u) for u in data.get("uris") or []][:2000]))

    @r.post("/api/announce")
    async def api_announce(request):
        data = await body(request)
        res = await flex.announcer.play(data.get("items") or data.get("url"), group=data.get("group") or None,
                                        wait=data.get("wait", True) is not False,
                                        timeout=float(data.get("timeout") or 900))
        return ok(res)

    @r.post("/api/announce/stop")
    async def api_announce_stop(_request):
        await flex.announcer.stop()
        return ok({"stopped": True})

    @r.post("/api/groups/{gid}/activate")
    async def api_group_activate(request):
        group = flex.groups.get(request.match_info["gid"])
        known = {s["id"] for s in await flex.speakers(True)}
        ids = [i for i in group["speakers"] if i in known]
        if not ids:
            raise SpotifyError(f"Kein Lautsprecher der Gruppe „{group['name']}“ ist gerade erreichbar.", 409)
        await flex.select_outputs(ids)
        result = await speakers_changed()
        missing = len(group["speakers"]) - len(ids)
        if missing:
            result["warning"] = f"{missing} Lautsprecher der Gruppe ist gerade nicht erreichbar."
        return ok(result)

    # ---- other Spotify Connect devices (optional hand-over)
    @r.get("/api/devices")
    async def api_devices(_request):
        return ok({"devices": await flex.api.devices(), "self": (flex.status or {}).get("device_id")})

    @r.post("/api/devices/transfer")
    async def api_transfer(request):
        data = await body(request)
        target = str(data.get("device_id") or (flex.status or {}).get("device_id") or "")
        if not target:
            raise ValueError("device_id fehlt")
        await flex.api.transfer(target, bool(data.get("play", True)))
        return ok()

    @r.get("/api/now/liked")
    async def api_now_liked(_request):
        uri = ((flex.status or {}).get("track") or {}).get("uri")
        if not uri or not flex.auth.connected:
            return ok({"uri": uri, "liked": None})
        return ok({"uri": uri, "liked": (await flex.api.library_contains([uri]) or [None])[0]})

    app.add_routes(r)
    return app


def main() -> None:
    web.run_app(build_app(), host="0.0.0.0", port=INGRESS_PORT, access_log=None, print=None)


if __name__ == "__main__":
    main()
