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

## 1.0.3
- Anmeldecode wird sofort angezeigt (go-librespot beantwortet /status erst nach dem Login).

## 1.0.4
- Netzwerk-Umgehung: nicht erreichbare Spotify-Server (z. B. gew4-spclient) werden automatisch auf eine funktionierende Spotify-IP umgeleitet; Prüfung beim Start und alle 30 Minuten.
- Verständliche Meldung, wenn ein HomePod die Verbindung ablehnt.
