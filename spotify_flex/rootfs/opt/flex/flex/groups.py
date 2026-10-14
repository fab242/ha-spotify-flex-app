"""Saved speaker groups (like Music Assistant's player groups), stored in /data."""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from .api import SpotifyError
from .const import GROUPS_FILE

_ID = re.compile(r"^[a-z0-9]{8,32}$")


class GroupStore:
    def __init__(self, path: str | None = None) -> None:
        self._path = Path(path or GROUPS_FILE)
        self._groups: list[dict] = self._load()

    def _load(self) -> list[dict]:
        try:
            data = json.loads(self._path.read_text())
        except (OSError, ValueError):
            return []
        out = []
        for g in data if isinstance(data, list) else []:
            if isinstance(g, dict) and _ID.match(str(g.get("id", ""))) and g.get("name"):
                out.append({"id": g["id"], "name": str(g["name"])[:60],
                            "speakers": [str(s) for s in g.get("speakers") or [] if str(s).isdigit()]})
        return out

    def _save(self) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._groups, ensure_ascii=False, indent=1))
        tmp.replace(self._path)

    @staticmethod
    def _clean(name: str, speakers: list) -> tuple[str, list[str]]:
        name = str(name or "").strip()[:60]
        if not name:
            raise SpotifyError("Bitte einen Namen für die Gruppe angeben.", 400)
        ids = []
        for s in speakers or []:
            s = str(s)
            if not s.isdigit():
                raise SpotifyError("Ungültige Lautsprecher-ID.", 400)
            if s not in ids:
                ids.append(s)
        if not ids:
            raise SpotifyError("Eine Gruppe braucht mindestens einen Lautsprecher.", 400)
        return name, ids

    def all(self) -> list[dict]:
        return [dict(g, speakers=list(g["speakers"])) for g in self._groups]

    def get(self, gid: str) -> dict:
        for g in self._groups:
            if g["id"] == gid:
                return dict(g, speakers=list(g["speakers"]))
        raise SpotifyError("Gruppe nicht gefunden.", 404)

    def create(self, name: str, speakers: list) -> dict:
        name, ids = self._clean(name, speakers)
        if any(g["name"].lower() == name.lower() for g in self._groups):
            raise SpotifyError(f"Es gibt schon eine Gruppe „{name}“.", 409)
        group = {"id": uuid.uuid4().hex[:12], "name": name, "speakers": ids}
        self._groups.append(group)
        self._save()
        return dict(group)

    def update(self, gid: str, name: str | None = None, speakers: list | None = None) -> dict:
        for g in self._groups:
            if g["id"] == gid:
                new_name, ids = self._clean(name if name is not None else g["name"],
                                            speakers if speakers is not None else g["speakers"])
                if any(o is not g and o["name"].lower() == new_name.lower() for o in self._groups):
                    raise SpotifyError(f"Es gibt schon eine Gruppe „{new_name}“.", 409)
                g["name"], g["speakers"] = new_name, ids
                self._save()
                return dict(g)
        raise SpotifyError("Gruppe nicht gefunden.", 404)

    def delete(self, gid: str) -> None:
        before = len(self._groups)
        self._groups = [g for g in self._groups if g["id"] != gid]
        if len(self._groups) == before:
            raise SpotifyError("Gruppe nicht gefunden.", 404)
        self._save()

    @staticmethod
    def active(groups: list[dict], speakers: list[dict]) -> str | None:
        """Id of the group whose speakers are exactly the selected ones, if any."""
        selected = {s["id"] for s in speakers if s.get("selected")}
        if not selected:
            return None
        for g in groups:
            if set(g["speakers"]) == selected:
                return g["id"]
        return None
