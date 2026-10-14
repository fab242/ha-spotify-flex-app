"""Glue to Home Assistant: API token, bundled integration install, discovery."""
from __future__ import annotations

import json
import logging
import os
import secrets
import shutil
from pathlib import Path

import aiohttp

from .const import (API_TOKEN_FILE, HA_CUSTOM_COMPONENTS, INGRESS_PORT, INTEGRATION_DOMAIN,
                    INTEGRATION_SRC, SUPERVISOR_URL)

_LOGGER = logging.getLogger("flex.bridge")


def api_token() -> str:
    """Token the HA integration uses for direct (non-ingress) calls."""
    path = Path(API_TOKEN_FILE)
    try:
        token = path.read_text().strip()
        if len(token) >= 32:
            return token
    except OSError:
        pass
    token = secrets.token_urlsafe(32)
    path.write_text(token)
    os.chmod(path, 0o600)
    return token


def _manifest_version(folder: Path) -> str | None:
    try:
        return json.loads((folder / "manifest.json").read_text()).get("version")
    except (OSError, ValueError):
        return None


def install_integration() -> str:
    """Copy the bundled integration into HA's custom_components when it changed.

    Returns 'installed', 'updated', 'current' or 'unavailable'.
    """
    src = Path(INTEGRATION_SRC)
    base = Path(HA_CUSTOM_COMPONENTS)
    if not src.is_dir() or not base.parent.is_dir():
        return "unavailable"
    dest = base / INTEGRATION_DOMAIN
    old = _manifest_version(dest)
    if old == _manifest_version(src):
        return "current"
    base.mkdir(exist_ok=True)
    tmp = base / f".{INTEGRATION_DOMAIN}.new"
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(src, tmp, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.rmtree(dest, ignore_errors=True)
    tmp.rename(dest)
    return "updated" if old else "installed"


def _supervisor_headers() -> dict | None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else None


async def push_discovery(session: aiohttp.ClientSession, token: str) -> bool:
    headers = _supervisor_headers()
    if not headers:
        return False
    payload = {"service": INTEGRATION_DOMAIN,
               "config": {"host": "127.0.0.1", "port": INGRESS_PORT, "token": token}}
    try:
        async with session.post(f"{SUPERVISOR_URL}/discovery", json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status >= 400:
                _LOGGER.warning("discovery failed: HTTP %s %s", resp.status, (await resp.text())[:200])
                return False
            return True
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.warning("discovery failed: %s", err)
        return False


async def notify(session: aiohttp.ClientSession, title: str, message: str) -> None:
    headers = _supervisor_headers()
    if not headers:
        return
    try:
        async with session.post(f"{SUPERVISOR_URL}/core/api/services/persistent_notification/create",
                                json={"title": title, "message": message,
                                      "notification_id": "spotify_flex_app"},
                                headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            await resp.read()
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.warning("notification failed: %s", err)
