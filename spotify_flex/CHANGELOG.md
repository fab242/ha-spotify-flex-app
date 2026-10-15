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

## 1.0.5
- Netzwerk-Umgehung leitet keine Spotify-Zugangspunkte (ap-*) mehr um – die haben ein eigenes Protokoll.

## 1.0.6

- HomePods mit HomePod-Software 27 lehnten die Verbindung mit „403 Forbidden“ ab: OwnTone meldet sich jetzt mit einem AirPlay-User-Agent (owntone #2042).

## 1.0.7

- Startprüfung, ob die AirPlay-2-Zeitports 319/320 frei sind (Music Assistant belegt sie ggf.).
- OwnTone protokolliert Warnungen; klarere Meldung, wenn ein Lautsprecher nicht verbindet (PIN, z. B. Apple TV).

## 1.1.0

- Lautsprecher-Gruppen: speichern, mit einem Tipp aktivieren, umbenennen, aktualisieren, löschen. Dazu ein Knopf „alle aus“.
- Neue Home-Assistant-Integration „Spotify Flex Player“ wird von der App mitgebracht und automatisch entdeckt: Player-Entität (Mediathek, Quelle/Gruppen, Gruppieren), eine Player-Entität je Lautsprecher und eine Auswahl für Gruppen.
- Direkter Zugriff von Home Assistant nur noch mit API-Token.

## 1.2.0

- Neue Player-Kachel `custom:spotify-flex-flow-card` im Aufbau von HOMEii Flow (helles Neumorph, ohne Logo/Farbverlauf, kein Ladeflackern): Cover mit Vorschau des nächsten Titels, Liedtext links (synchron, AirPlay-Verzögerung einstellbar), Mediathek mit Suche, Warteschlange, Lieblingssong, Sleep-Timer, Lautsprecher und Gruppen.
- Integration: Dienste `search`, `queue`, `add_to_queue`, `like`, `sleep_timer` (mit Antwort); die Kachel wird unter `/spotify_flex_app/spotify-flex-flow-card.js` bereitgestellt.

## 1.2.1

- Player-Kachel: eigener Knopf „Lautsprecher / Gruppe“, pro Box „Nur hier“, Schatten wie die übrigen Kacheln; Lautsprecher werden direkt über den Player gefunden.

## 1.2.2

- Player-Kachel: Lautsprecher-Anzeige oben links entfernt (Auswahl über den Lautsprecher-Knopf).

## 1.3.0

- Liedtext mit springendem Punkt: landet auf jedem Wort, wenn es gesungen wird (Wortzeiten aus erweitertem LRC, sonst nach Silben geschätzt); gesungene Wörter werden dunkel.
- Genauere Synchronisierung: Uhrabweichung zwischen Browser und Home Assistant wird ausgeglichen; Knopf „Takt“ misst den Versatz, wenn man beim Zeilenanfang tippt.

## 1.4.0

- Liedtext synchron zum hörbaren Ton: Die App meldet OwnTone über die Metadaten-Pipe die Spotify-Position und misst daraus die tatsächliche Verzögerung (Pipe, OwnTone-Puffer, AirPlay). Player-Position in Home Assistant = was gerade zu hören ist (auf Millisekunden, mit Messzeitpunkt).
- Knopf „Takt“ entfernt; −/+ nur noch zur Feinkorrektur (0,1 s).

## 1.4.1

- Künstler öffnen: „Spotify: Invalid limit“ behoben – Spotify liefert dort seit Februar 2026 höchstens 10 Alben pro Abruf (weitere über „Mehr laden“).
