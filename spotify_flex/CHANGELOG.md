# Changelog

## 1.0.0
- Erste Version: go-librespot-Empfänger (Geräte-Code-Login), OwnTone-AirPlay-Ausgabe, Oberfläche mit Bibliothek, Playlists, Suche, Warteschlange, Lautsprechern und API-Konsole.

## 1.0.1
- Basis auf das offizielle Home-Assistant-Image (Alpine 3.22) umgestellt; das linuxserver-Image gibt es für ARM nicht mehr.
- OwnTone 29.3 und go-librespot v0.9.1 werden beim Installieren selbst kompiliert.
- Avahi veröffentlicht keine eigenen Hostnamen (kein Konflikt mit homeassistant.local).

## 1.0.2
- OwnTone: fehlendes htdocs-Verzeichnis ergänzt (Absturz beim Start behoben).
- Avahi: keine SSH-Dienste mehr veröffentlichen.
