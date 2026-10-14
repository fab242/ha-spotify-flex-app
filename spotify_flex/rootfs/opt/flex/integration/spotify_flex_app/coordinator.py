"""Keeps the app state: WebSocket push plus a slow poll as safety net."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import FlexAuthError, FlexClient, FlexError
from .const import DOMAIN, POLL_SECONDS

_LOGGER = logging.getLogger(__name__)


class FlexCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: FlexClient) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN,
                         update_interval=timedelta(seconds=POLL_SECONDS))
        self.client = client
        self._stop = asyncio.Event()
        self._ws_task: asyncio.Task | None = None

    async def _async_update_data(self) -> dict:
        try:
            return await self.client.state()
        except FlexAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except FlexError as err:
            raise UpdateFailed(str(err)) from err

    def start_push(self) -> None:
        self._ws_task = self.config_entry.async_create_background_task(
            self.hass, self.client.events(self._on_message, self._stop), f"{DOMAIN}_ws")

    async def stop_push(self) -> None:
        self._stop.set()
        if self._ws_task:
            self._ws_task.cancel()

    async def _on_message(self, msg: dict) -> None:
        if not self.data:
            return
        kind, payload = msg.get("type"), msg.get("data")
        if kind == "status" and isinstance(payload, dict):
            self.async_set_updated_data(dict(self.data, player=payload))
        elif kind == "speakers" and isinstance(payload, dict):
            new = dict(self.data)
            for key in ("speakers", "groups", "active_group"):
                if key in payload:
                    new[key] = payload[key]
            self.async_set_updated_data(new)

    # ---- commands (always followed by a fresh state)
    async def command(self, method: str, path: str, body=None) -> dict | None:
        try:
            result = await self.client.request(method, path, body)
        except FlexError as err:
            from homeassistant.exceptions import HomeAssistantError
            raise HomeAssistantError(str(err)) from err
        if isinstance(result, dict) and "speakers" in result and self.data:
            new = dict(self.data)
            for key in ("speakers", "groups", "active_group"):
                if key in result:
                    new[key] = result[key]
            if "player" in result:
                new["player"] = result["player"]
            self.async_set_updated_data(new)
        elif isinstance(result, dict) and "player" in result and self.data:
            self.async_set_updated_data(dict(self.data, player=result["player"]))
        return result

    # ---- helpers
    @property
    def speakers(self) -> list[dict]:
        return (self.data or {}).get("speakers") or []

    @property
    def groups(self) -> list[dict]:
        return (self.data or {}).get("groups") or []

    @property
    def player(self) -> dict:
        return (self.data or {}).get("player") or {}

    def selected_ids(self) -> list[str]:
        return [s["id"] for s in self.speakers if s.get("selected")]
