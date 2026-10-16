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

## 1.5.0

- Player: im Reiter „Playlists“ öffentliche Playlists suchen, abspielen, öffnen und über ⋮ → „Zu meinen Playlists“ speichern.
- Gespeicherte Titel/Playlists erscheinen sofort in der Bibliothek (Cache wird geleert).

## 1.5.1

- Suche akzeptiert Spotify-Links/URIs („Teilen → Link kopieren“): damit lassen sich auch Spotify-eigene Playlists wie „This Is …“ abspielen, die die Web-API seit Ende 2024 nicht mehr herausgibt.

## 1.5.2

- Liedtext nach Liedwechsel: lrclib meldet neue Titel beim ersten Abruf oft als „nicht gefunden“ – die Kachel fragt jetzt nach 6 und 20 s erneut nach (zeigt „Liedtext wird gesucht …“) und bricht hängende Abrufe nach 15 s ab.

## 1.6.0

- App-Seite ist jetzt eine reine Einstellungsseite im Design des aktiven Home-Assistant-Themes (hell/dunkel, Farben, Karten): Konten, Lautsprecher, Gruppen, System. Player und Bibliothek gibt es nur noch in der Kachel.
- Lautsprecher konfigurieren: Anzeigename, Lautstärke beim Einschalten, maximale Lautstärke, ausblenden, Koppeln per PIN (z. B. Apple TV).
- Gruppen anlegen, umbenennen, Mitglieder ändern, löschen (beliebig viele).
- Integration: Namensänderungen benennen auch das Gerät in Home Assistant um.

## 1.6.1

- Einstellungsseite: Gestaltung und Programm werden nach einem Update nicht mehr aus dem Browser-Zwischenspeicher geladen (Seite blieb sonst leer im alten Design).

## 1.6.2

- Einstellungsseite: Lautsprecher-Gruppen stehen jetzt im Reiter „Lautsprecher“ unter den Lautsprechern; der eigene Reiter „Gruppen“ entfällt.

## 1.6.3

- Einstellungsseite, Reiter „System“: Gerätename, Klangqualität und Lautstärke-Normalisierung direkt einstellbar. Die Werte bleiben die App-Optionen (auch unter Konfiguration sichtbar); beim Speichern startet nur der Spotify-Empfänger kurz neu, nicht die ganze App.

## 1.6.4

- Klangqualität: Wert wird im Format der App-Optionen gespeichert (Text statt Zahl).

## 1.6.5

- Klangqualität: Auswahlliste im HA-Design (vorher heller Hintergrund mit heller Schrift im dunklen Design).

## 1.7.0

- Neu: **Equalizer** (Reiter „Equalizer“ der Einstellungsseite) mit 6 Bändern (60 Hz – 15 kHz, ±12 dB) und 22 Voreinstellungen wie in der Spotify-App. Kurve mit der Maus/dem Finger ziehen oder Voreinstellung wählen – Änderungen wirken sofort und ohne Unterbrechung auf allen Lautsprechern.
- Audio läuft dafür durch den neuen Dienst `flex-eq` (go-librespot → Equalizer → OwnTone). Automatischer Headroom und weicher Limiter verhindern Übersteuern bei Anhebungen.

## 1.7.1

- Player-Kachel: neuer Button **Equalizer** (Regler-Symbol, grün wenn an) – Kurve ziehen, Voreinstellungen wählen, ein/aus; wirkt sofort.
- Integration: neuer Dienst `spotify_flex_app.equalizer` (abfragen oder einstellen, z. B. in Automationen). Nach dem Update Home Assistant einmal neu starten.

## 1.7.2

- Equalizer: Anhebungen (z. B. Bass-Booster) machen Stimmen und Mitten nicht mehr leiser. Statt die ganze Lautstärke um bis zu 5 dB abzusenken, fängt jetzt ein Look-ahead-Limiter (5,8 ms) nur die Spitzen ab, die übersteuern würden.

## 1.7.3

- Liedtext: flüssiger Zeilenwechsel – die Zeilen rollen weich weiter (eigene Ease-Animation statt Sprung), die aktuelle Zeile wird sanft hervorgehoben (kein Fettschrift-Sprung mehr), der Zeilenwechsel wird im Bildtakt statt alle 250 ms erkannt, und der springende Punkt hüpft am Zeilenende im Bogen zum ersten Wort der nächsten Zeile.

## 1.7.4

- Player-Kachel: in Playlists, Alben usw. neben „Alles abspielen“ jetzt auch **„Zufällig abspielen“** (startet mit einem zufälligen Titel, Zufallswiedergabe an). „Alles abspielen“ spielt in Reihenfolge.

## 1.7.5

- Player-Kachel: Hintergrund färbt sich passend zum Cover des laufenden Titels (zarter Farbton der prägenden Cover-Farbe, weicher Übergang beim Titelwechsel; Neumorph-Schatten passen sich an). Ohne Cover bleibt er weiß, bei schwarz-weißen Covern hellgrau.

## 1.7.6

- Player-Kachel: Hintergrund als **Farbverlauf aus den Cover-Farben** (bis zu drei prägende Farbtöne, bündig über die ganze Kachel, weiches Überblenden beim Titelwechsel). Knöpfe und Regler sind leicht durchscheinend, damit der Verlauf sichtbar bleibt. Ohne Cover weiß.
