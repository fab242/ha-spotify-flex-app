"""Receiver settings editable on the configuration page (device name, quality, normalisation).

The values stay the app options of Home Assistant (single source of truth, also visible under
Einstellungen -> Apps -> Spotify Flex -> Konfiguration). Saving writes them to the Supervisor,
rewrites the go-librespot configuration and restarts only the Spotify receiver - not the app.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path

import aiohttp

from .const import LIBRESPOT_CONFIG, LIBRESPOT_SERVICE, OPTIONS_FILE, SUPERVISOR_URL

_LOGGER = logging.getLogger("flex.appopts")

BITRATES = (96, 160, 320)
DEFAULTS = {"device_name": "Home Flex", "bitrate": 320, "normalisation": True}
NAME_MAX = 60


class OptionsError(ValueError):
    """Invalid value or the Supervisor refused the change."""


def receiver_settings(options: dict) -> dict:
    out = {key: options.get(key, default) for key, default in DEFAULTS.items()}
    try:  # the Supervisor keeps list(96|160|320) options as strings
        out["bitrate"] = int(out["bitrate"])
    except (TypeError, ValueError):
        out["bitrate"] = DEFAULTS["bitrate"]
    return out


def validate(changes: dict) -> dict:
    out: dict = {}
    if "device_name" in changes:
        name = re.sub(r"\s+", " ", str(changes["device_name"] or "")).strip()
        if not name:
            raise OptionsError("Der Gerätename darf nicht leer sein.")
        if len(name) > NAME_MAX:
            raise OptionsError(f"Der Gerätename darf höchstens {NAME_MAX} Zeichen haben.")
        if any(c in name for c in '"\\') or any(ord(c) < 32 for c in name):
            raise OptionsError("Der Gerätename enthält ungültige Zeichen.")
        out["device_name"] = name
    if "bitrate" in changes:
        try:
            rate = int(changes["bitrate"])
        except (TypeError, ValueError):
            rate = 0
        if rate not in BITRATES:
            raise OptionsError("Klangqualität muss 96, 160 oder 320 kbit/s sein.")
        out["bitrate"] = rate
    if "normalisation" in changes:
        if not isinstance(changes["normalisation"], bool):
            raise OptionsError("Lautstärke-Normalisierung muss an oder aus sein.")
        out["normalisation"] = changes["normalisation"]
    return out


def render_librespot(text: str, settings: dict) -> str:
    """Replace the three keys in the generated go-librespot config.yml."""
    repl = {
        "device_name": f'"{settings["device_name"]}"',
        "bitrate": str(settings["bitrate"]),
        "normalisation_disabled": "false" if settings["normalisation"] else "true",
    }
    for key, value in repl.items():
        text, n = re.subn(rf"(?m)^{key}:.*$", lambda _m, k=key, v=value: f"{k}: {v}", text)
        if not n:
            text = text.rstrip("\n") + f"\n{key}: {value}\n"
    return text


async def push_supervisor(session: aiohttp.ClientSession, options: dict) -> None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise OptionsError("Kein Zugriff auf den Supervisor – Einstellung nicht gespeichert.")
    try:
        async with session.post(f"{SUPERVISOR_URL}/addons/self/options", json={"options": options},
                                headers={"Authorization": f"Bearer {token}"},
                                timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status >= 400:
                text = (await resp.text())[:300]
                _LOGGER.warning("saving app options failed: HTTP %s %s", resp.status, text)
                raise OptionsError(f"Home Assistant hat die Einstellung abgelehnt (HTTP {resp.status}).")
    except (aiohttp.ClientError, TimeoutError) as err:
        raise OptionsError(f"Supervisor nicht erreichbar: {err}") from err


async def restart_receiver() -> bool:
    try:
        proc = await asyncio.create_subprocess_exec("/command/s6-svc", "-r", LIBRESPOT_SERVICE,
                                                    stdout=asyncio.subprocess.DEVNULL,
                                                    stderr=asyncio.subprocess.PIPE)
        _out, err = await asyncio.wait_for(proc.communicate(), 10)
        if proc.returncode:
            _LOGGER.warning("receiver restart failed: %s", err.decode(errors="replace").strip())
        return proc.returncode == 0
    except (OSError, asyncio.TimeoutError) as err:
        _LOGGER.warning("receiver restart failed: %s", err)
        return False


async def apply(session: aiohttp.ClientSession, options: dict, changes: dict) -> tuple[dict, bool]:
    """Save changes; returns (new options, receiver restarted)."""
    clean = validate(changes)
    current = receiver_settings(options)
    if not clean or all(current[k] == v for k, v in clean.items()):
        return options, False
    merged = {**options, **clean}
    if "bitrate" in merged:  # schema list(...) -> the Supervisor expects the string form
        merged["bitrate"] = str(merged["bitrate"])
    await push_supervisor(session, merged)
    try:  # Supervisor writes options.json only on the next start - keep ours in step
        tmp = Path(OPTIONS_FILE + ".tmp")
        tmp.write_text(json.dumps(merged))
        tmp.replace(OPTIONS_FILE)
    except OSError as err:
        _LOGGER.warning("could not update %s: %s", OPTIONS_FILE, err)
    cfg = Path(LIBRESPOT_CONFIG)
    try:
        cfg.write_text(render_librespot(cfg.read_text(), receiver_settings(merged)))
    except OSError as err:
        _LOGGER.warning("could not update %s: %s", cfg, err)
        return merged, False
    return merged, await restart_receiver()
