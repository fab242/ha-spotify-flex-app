"""HTTP/WebSocket client for the Spotify Flex app (runs on the HA host)."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

import aiohttp

_LOGGER = logging.getLogger(__name__)


class FlexError(Exception):
    """Error reported by the app (message is user facing, German)."""


class FlexAuthError(FlexError):
    """Token rejected."""


class FlexClient:
    def __init__(self, session: aiohttp.ClientSession, host: str, port: int, token: str) -> None:
        self._s = session
        self._base = f"http://{host}:{port}"
        self._headers = {"Authorization": f"Bearer {token}"}
        self._token = token

    async def request(self, method: str, path: str, body: Any = None, params: dict | None = None,
                      timeout: float = 20) -> Any:
        try:
            async with self._s.request(method, self._base + path, json=body, params=params,
                                       headers=self._headers,
                                       timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                text = await resp.text()
                data = None
                if text:
                    try:
                        data = json.loads(text)
                    except ValueError:
                        data = None
                if resp.status == 401:
                    raise FlexAuthError("Der API-Token der Spotify-Flex-App passt nicht.")
                if resp.status >= 400:
                    msg = (data or {}).get("error") if isinstance(data, dict) else None
                    raise FlexError(msg or f"Spotify Flex: HTTP {resp.status}")
                return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise FlexError(f"Spotify-Flex-App nicht erreichbar ({type(err).__name__}).") from err

    async def state(self) -> dict:
        return await self.request("GET", "/api/state")

    async def events(self, on_message: Callable[[dict], Awaitable[None]], stop: asyncio.Event) -> None:
        """Follow the app's WebSocket; reconnect with backoff until stopped."""
        delay = 2
        while not stop.is_set():
            try:
                async with self._s.ws_connect(self._base.replace("http", "ws") + "/ws",
                                              params={"token": self._token}, heartbeat=30) as ws:
                    delay = 2
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                await on_message(json.loads(msg.data))
                            except ValueError:
                                pass
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
                _LOGGER.debug("websocket: %s", err)
            if stop.is_set():
                return
            await asyncio.sleep(delay)
            delay = min(60, delay * 2)
