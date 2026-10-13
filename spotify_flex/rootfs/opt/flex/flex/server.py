"""Spotify Flex app: HTTP/WebSocket backend behind Home Assistant ingress."""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web
import aiohttp

from .api import SpotifyAuthError, SpotifyClient, SpotifyError, valid_id
from .browse import browse
from .const import INGRESS_PORT, LIBRESPOT_STATE, OPTIONS_FILE, REDIRECT_URI, VERSION
from .oauth import WebAuth
from .receiver import Librespot, OwnTone

logging.basicConfig(level=logging.INFO, format="[spotify-flex] %(levelname)s %(message)s")
_LOGGER = logging.getLogger("flex")

STATIC = Path(__file__).resolve().parent.parent / "static"
ALLOWED_PEERS = {"172.30.32.2", "127.0.0.1", "::1"}  # Supervisor ingress proxy + local


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
        self.auth: WebAuth | None = None
        self.api: SpotifyClient | None = None
        self.status: dict | None = None
        self.sockets: set[web.WebSocketResponse] = set()
        self.stop = asyncio.Event()
        self.tasks: list[asyncio.Task] = []
        self.auth_pending: dict | None = None  # device-code login in progress

    # ------------------------------------------------------------ lifecycle
    async def start(self, _app: web.Application) -> None:
        self.session = aiohttp.ClientSession()
        self.receiver = Librespot(self.session)
        self.owntone = OwnTone(self.session)
        self.auth = WebAuth(self.session, self.options.get("client_id", ""))
        self.api = SpotifyClient(self.session, self.auth.token)
        self.tasks = [
            asyncio.create_task(self.receiver.events(self.on_event, self.stop)),
            asyncio.create_task(self.poll_status()),
        ]

    async def shutdown(self, _app: web.Application) -> None:
        self.stop.set()
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
            except SpotifyError:
                self.status = None
        if broadcast:
            await self.broadcast({"type": "status", "data": self.player_view()})
        return self.status or {}

    async def on_event(self, event: dict) -> None:
        kind = event.get("type")
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
                "position_ms": track.get("position"),
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
            speakers = await self.owntone.outputs()
        except SpotifyError as err:
            speaker_error = str(err)
        return {
            "version": VERSION,
            "receiver": {"running": receiver_ok, "logged_in": logged_in or bool(self.status),
                         "auth_code": auth_code},
            "web": {"configured": self.auth.configured, "connected": self.auth.connected,
                    "redirect_uri": REDIRECT_URI},
            "player": self.player_view(),
            "speakers": speakers,
            "speaker_error": speaker_error,
        }

    def user_id(self) -> str:
        return (self.status or {}).get("username") or ""


# ---------------------------------------------------------------- web layer
def build_app() -> web.Application:
    flex = App()

    @web.middleware
    async def guard(request: web.Request, handler):
        peer = request.remote or ""
        if peer not in ALLOWED_PEERS:
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

    # ---- static UI
    @r.get("/")
    async def index(_request):
        resp = web.FileResponse(STATIC / "index.html")
        resp.headers["Cache-Control"] = "no-store"
        return resp

    r.static("/static", STATIC)

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
        if uri == "liked":
            uri = f"spotify:user:{flex.user_id()}:collection"
        if context and context != uri:
            await flex.receiver.play(context, skip_to_uri=uri)
        else:
            await flex.receiver.play(uri)
        warning = None
        try:
            if not any(o["selected"] for o in await flex.owntone.outputs()):
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
        status = await flex.refresh_status(broadcast=True)
        return ok({"player": flex.player_view(), "raw": bool(status)})

    # ---- speakers (OwnTone outputs)
    @r.get("/api/speakers")
    async def api_speakers(_request):
        return ok({"speakers": await flex.owntone.outputs()})

    @r.post("/api/speakers/{oid}")
    async def api_speaker_set(request):
        data = await body(request)
        await flex.owntone.set_output(request.match_info["oid"], selected=data.get("selected"),
                                      volume=data.get("volume"), pin=data.get("pin"))
        return ok({"speakers": await flex.owntone.outputs()})

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
