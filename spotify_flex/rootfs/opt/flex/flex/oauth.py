"""Spotify Web API login with PKCE (only the client ID of the user's own developer app is needed).

Spotify only accepts plain-http redirect URIs on the loopback address, and the
app runs headless, so the flow is: open the authorize URL, approve, the browser
lands on http://127.0.0.1:8765/callback?code=... (which does not load), the
user pastes that address into the app. The code is exchanged here.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import aiohttp

from .api import SpotifyAuthError, SpotifyError
from .const import AUTHORIZE_URL, REDIRECT_URI, SCOPES, TOKEN_FILE, TOKEN_URL


class WebAuth:
    def __init__(self, session: aiohttp.ClientSession, client_id: str, token_file: str = TOKEN_FILE) -> None:
        self._session = session
        self.client_id = (client_id or "").strip()
        self._file = Path(token_file)
        self._token: dict = {}
        self._pending: dict[str, str] = {}  # state -> verifier
        self._lock = asyncio.Lock()
        try:
            data = json.loads(self._file.read_text())
            if data.get("client_id") == self.client_id:
                self._token = data
        except (OSError, ValueError):
            pass

    # ------------------------------------------------------------------ state
    @property
    def configured(self) -> bool:
        return bool(self.client_id)

    @property
    def connected(self) -> bool:
        return bool(self._token.get("refresh_token"))

    def _save(self) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps({**self._token, "client_id": self.client_id}))
        os.chmod(tmp, 0o600)
        tmp.replace(self._file)

    def logout(self) -> None:
        self._token = {}
        try:
            self._file.unlink()
        except OSError:
            pass

    # ------------------------------------------------------------------- flow
    def authorize_url(self) -> str:
        if not self.configured:
            raise SpotifyError("In den App-Optionen fehlt die Client-ID deiner Spotify-Entwickler-App.", 400)
        verifier = secrets.token_urlsafe(64)[:96]
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        state = secrets.token_urlsafe(16)
        self._pending = {state: verifier}  # only the latest attempt is valid
        return AUTHORIZE_URL + "?" + urlencode({
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
            "state": state,
            "scope": " ".join(SCOPES),
            "show_dialog": "true",
        })

    async def finish(self, pasted: str) -> None:
        """Accept the full redirect address (or just the code) the user pasted."""
        text = (pasted or "").strip()
        code, state = text, None
        if "code=" in text or "error=" in text:
            query = parse_qs(urlparse(text).query or text.split("?", 1)[-1])
            if "error" in query:
                raise SpotifyError(f"Spotify hat die Anmeldung abgelehnt: {query['error'][0]}", 400)
            code = (query.get("code") or [""])[0]
            state = (query.get("state") or [None])[0]
        if not code:
            raise SpotifyError("Im eingefügten Text steht kein Anmeldecode.", 400)
        if state is not None and state not in self._pending:
            raise SpotifyError("Diese Anmeldung gehört zu einem älteren Versuch. Bitte neu starten.", 400)
        verifier = self._pending.get(state) if state else next(iter(self._pending.values()), None)
        if not verifier:
            raise SpotifyError("Bitte zuerst auf „Mit Spotify anmelden“ tippen.", 400)
        token = await self._post({
            "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI,
            "client_id": self.client_id, "code_verifier": verifier,
        })
        self._pending = {}
        self._store(token)

    # ----------------------------------------------------------------- tokens
    def _store(self, token: dict, keep_refresh: str | None = None) -> None:
        if not token.get("access_token"):
            raise SpotifyAuthError("Spotify hat kein Zugriffstoken geliefert.", 401)
        self._token = {
            "access_token": token["access_token"],
            "refresh_token": token.get("refresh_token") or keep_refresh,
            "expires_at": time.time() + int(token.get("expires_in", 3600)) - 60,
            "scope": token.get("scope", ""),
        }
        self._save()

    async def _post(self, form: dict) -> dict:
        try:
            async with self._session.post(TOKEN_URL, data=form, allow_redirects=False,
                                          timeout=aiohttp.ClientTimeout(total=20)) as resp:
                data = await resp.json(content_type=None)
                if resp.status == 200 and isinstance(data, dict):
                    return data
                msg = (data or {}).get("error_description") or (data or {}).get("error") or f"HTTP {resp.status}"
                if resp.status in (400, 401):
                    raise SpotifyAuthError(f"Spotify-Anmeldung abgelehnt: {msg}", 401)
                raise SpotifyError(f"Spotify-Tokenserver: {msg}", resp.status)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise SpotifyError("Spotify-Tokenserver nicht erreichbar.") from err

    async def token(self) -> str:
        """Valid access token for the Web API client."""
        if not self.connected:
            raise SpotifyAuthError("Spotify-Bibliothek ist noch nicht verbunden.", 401)
        async with self._lock:
            if time.time() < self._token.get("expires_at", 0):
                return self._token["access_token"]
            refresh = self._token["refresh_token"]
            try:
                data = await self._post({"grant_type": "refresh_token", "refresh_token": refresh,
                                         "client_id": self.client_id})
            except SpotifyAuthError:
                self.logout()
                raise
            self._store(data, keep_refresh=refresh)
            return self._token["access_token"]
