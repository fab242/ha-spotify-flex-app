# Spotify Flex

Eigenständiger Spotify-Player für Home Assistant – ohne Handy, ohne Music Assistant.

* **Empfänger:** go-librespot meldet sich als Spotify-Connect-Gerät „Home Flex“ an und bleibt dauerhaft verfügbar.
* **Lautsprecher:** OwnTone schickt den Ton per AirPlay 2 an deine HomePods – einzeln oder mehrere synchron, je mit eigener Lautstärke.
* **Bedienung:** eigene Seite in der Seitenleiste mit Wiedergabe, Lautsprechern, Bibliothek, Playlists (anlegen, bearbeiten, sortieren), Lieblingssongs, Alben, Künstlern, Podcasts, Suche, Warteschlange und direktem Zugriff auf jeden Endpunkt der Spotify-Web-API.

## Einrichtung

1. **Client-ID eintragen:** Im [Spotify-Entwickler-Dashboard](https://developer.spotify.com/dashboard) deine App öffnen, die *Client ID* kopieren und hier unter *Konfiguration* eintragen. Ein Client-Secret ist nicht nötig.
2. **Redirect-URI ergänzen:** In derselben App unter *Redirect URIs* `http://127.0.0.1:8765/callback` hinzufügen und speichern.
3. App starten und **Spotify** in der Seitenleiste öffnen. Die Seite führt durch:
   * **Empfänger anmelden:** Link öffnen (oder `spotify.com/pair`) und den angezeigten Code bestätigen. Einmalig.
   * **Bibliothek verbinden:** Mit Spotify anmelden, die Adresse der danach nicht ladenden Seite (`http://127.0.0.1:8765/callback?code=…`) kopieren und einfügen. Einmalig.
   * **Lautsprecher einschalten.**

## Einstellungsseite

Die Seite der App (Seitenleiste „Spotify Flex“) enthält nur Einstellungen und übernimmt das aktive Home-Assistant-Design:

* **Konten:** Spotify-Empfänger und Bibliothek anmelden oder trennen.
* **Lautsprecher:** Anzeigename, Lautstärke beim Einschalten, maximale Lautstärke, ausblenden; Geräte mit PIN (z. B. Apple TV) koppeln.
* **Gruppen:** beliebig viele Gruppen anlegen, umbenennen, Mitglieder ändern, löschen. Eine Gruppe schaltet genau ihre Lautsprecher ein und alle anderen aus.
* **System:** Status der Home-Assistant-Integration, gemessene Audio-Verzögerung, API-Token, Netzwerkbericht.

Abgespielt wird über die Player-Kachel bzw. die Home-Assistant-Entitäten.

## Home Assistant (Kacheln, Automationen)

Die App installiert automatisch die Integration **Spotify Flex Player** (abschaltbar über die Option *Home-Assistant-Player*). Nach dem ersten Start einmal Home Assistant neu starten. Danach erscheint sie unter *Einstellungen → Geräte & Dienste* als „Entdeckt“ und wird mit einem Klick hinzugefügt.

Sie legt an:

* `media_player.spotify_flex_player`: Wiedergabe, Lautstärke, Zufall und Wiederholen, Mediathek durchsuchen, Quelle (Gruppen und einzelne Lautsprecher) und Gruppieren über den Standard-Dialog von Home Assistant.
* je Lautsprecher einen Player, z. B. `media_player.badezimmer_spotify_flex`: ein- und ausschalten, eigene Lautstärke, zur Wiedergabe hinzufügen (*Gruppieren*).
* `select.spotify_flex_lautsprecher_gruppe`: gespeicherte Gruppe wählen oder „Aus“.

Die Integration spricht nur lokal mit der App (127.0.0.1, mit eigenem Token).

### Player-Kachel

Die Integration bringt die Kachel **Spotify Flex Flow** mit (Aufbau wie HOMEii Flow). Ressource: `/spotify_flex_app/spotify-flex-flow-card.js` (Typ *JavaScript-Modul*). Karte:

```yaml
type: custom:spotify-flex-flow-card
entity: media_player.spotify_flex_player
height: 600          # optional
lyrics_offset: 2.3   # optional: Sekunden AirPlay-Verzögerung für den Liedtext
cover_flow: true     # optional: nächstes Cover neben dem aktuellen
```

Liedtexte kommen von lrclib.net (Titel, Künstler, Album und Dauer werden dorthin gesendet). Ein springender Punkt landet auf jedem Wort, wenn es gesungen wird. Die Verzögerung zwischen Spotify und dem Lautsprecher misst die App laufend selbst (Attribut `audio_latency_ms` am Player); −/+ unter dem Liedtext ist nur noch Feinkorrektur. Zeilenanfänge kommen von lrclib.net, die Wortzeiten innerhalb einer Zeile werden nach Silben geschätzt.

## Voraussetzungen und Grenzen

* Spotify Premium.
* **Music Assistant darf nicht gleichzeitig laufen.** Für AirPlay 2 belegt es dieselben Zeitports 319/320 wie diese App. Beim Start meldet das Protokoll, ob die Ports frei sind.
* HomePods im selben Netz. Falls ein HomePod nicht reagiert: in der Home-App unter *Zuhause-Einstellungen → Lautsprecher und TV* den Zugriff auf „Alle im selben Netzwerk“ stellen.
* Die Web-API läuft über deine eigene Entwickler-App. Spotify-Kontingente und Einschränkungen des Entwicklungsmodus gelten weiter.
* AirPlay hat etwa 2 Sekunden Verzögerung zwischen Tippen und Ton.
