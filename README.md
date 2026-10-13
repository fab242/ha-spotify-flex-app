# Spotify Flex – Home-Assistant-App

Eigenständiger Spotify-Player für Home Assistant: eigener Spotify-Connect-Empfänger (go-librespot), AirPlay-2-Ausgabe an HomePods (OwnTone) und eine Bedienoberfläche in der Seitenleiste mit dem vollen Umfang der Spotify-Web-API.

## Installation

1. Home Assistant → **Einstellungen → Apps → App-Store → ⋮ → Repositorys**
2. `https://github.com/fab242/ha-spotify-flex-app` hinzufügen
3. **Spotify Flex** installieren, Client-ID eintragen, starten – Details in [DOCS.md](spotify_flex/DOCS.md).

## Aufbau

```
Spotify ──► go-librespot (Connect-Empfänger, Geräte-Code-Login)
                │  PCM-Pipe
                ▼
             OwnTone ──AirPlay 2──► HomePods
                ▲
Oberfläche ─────┘ (aiohttp-Backend: Web-API, Empfänger, Lautsprecher)
```

## Entwicklung

```bash
pip install pytest aiohttp && pytest -q
npm install happy-dom && node tests/test_ui.mjs
```
