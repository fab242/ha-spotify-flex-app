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
* **Lautsprecher-Gruppen** (im Reiter Lautsprecher, unter den Lautsprechern): beliebig viele Gruppen anlegen, umbenennen, Mitglieder ändern, löschen. Eine Gruppe schaltet genau ihre Lautsprecher ein und alle anderen aus.
* **Equalizer:** 6 Bänder (60 Hz, 150 Hz, 400 Hz, 1 kHz, 2,4 kHz, 15 kHz, je ±12 dB) und Voreinstellungen wie in der Spotify-App (Akustik, Bass-Booster, Klassik, Rock, Gesangs-Booster …). Punkte der Kurve ziehen (oder mit den Pfeiltasten verstellen) – die Änderung ist sofort auf allen Lautsprechern zu hören, ohne Unterbrechung. Anhebungen machen den Rest nicht leiser: Nur Spitzen, die übersteuern würden, fängt ein unhörbarer Begrenzer (Limiter) ab.
* **System:** Gerätename, Klangqualität und Lautstärke-Normalisierung des Spotify-Empfängers (beim Speichern startet nur der Empfänger kurz neu), Status der Home-Assistant-Integration, gemessene Audio-Verzögerung, API-Token, Netzwerkbericht.

Abgespielt wird über die Player-Kachel bzw. die Home-Assistant-Entitäten.

## Home Assistant (Kacheln, Automationen)

Die App installiert automatisch die Integration **Spotify Flex Player** (abschaltbar über die Option *Home-Assistant-Player*). Nach dem ersten Start einmal Home Assistant neu starten. Danach erscheint sie unter *Einstellungen → Geräte & Dienste* als „Entdeckt“ und wird mit einem Klick hinzugefügt.

Sie legt an:

* `media_player.spotify_flex_player`: Wiedergabe, Lautstärke, Zufall und Wiederholen, Mediathek durchsuchen, Quelle (Gruppen und einzelne Lautsprecher) und Gruppieren über den Standard-Dialog von Home Assistant.
* je Lautsprecher einen Player, z. B. `media_player.badezimmer_spotify_flex`: ein- und ausschalten, eigene Lautstärke, zur Wiedergabe hinzufügen (*Gruppieren*).
* `select.spotify_flex_lautsprecher_gruppe`: gespeicherte Gruppe wählen oder „Aus“.

Die Integration spricht nur lokal mit der App (127.0.0.1, mit eigenem Token).

### Player-Kachel

Die Kachel **Spotify Flex Flow** ist ein eigenes HACS-Paket: [fab242/spotify-flex-flow-card](https://github.com/fab242/spotify-flex-flow-card) (HACS → Benutzerdefinierte Repositories → Typ *Dashboard*). Alle Einstellungen gibt es im visuellen Editor der Karte.

### Liedtext exakt (Liedtext-Analyse)

Mit dem Container **flex-lyrics-aligner** im Heimnetz (z. B. auf Unraid, Anleitung im Repo [fab242/flex-lyrics-aligner](https://github.com/fab242/flex-lyrics-aligner)) legt eine lokale KI den Liedtext Wort für Wort an die gespielte Aufnahme an. Zeilenwechsel und springender Punkt sitzen dann auf etwa 1/20 s genau.

* Unter *Konfiguration* → *Liedtext-Analyse (Adresse)* die Adresse eintragen, z. B. `http://192.168.0.83:8770`.
* Jeder Titel wird beim ersten Abspielen analysiert, während er läuft; ab dem zweiten Mal ist er exakt. In Playlists zeigt die Kachel, wie viele Titel schon exakt sind.
* Vorab (ohne Abspielen) geht es nicht: Spotify gibt das Audio nur während der Wiedergabe heraus, und Mitschneiden verbieten die Spotify-Regeln.
* Gespeichert werden nur Wortzeiten, kein Audio. Zeilen, bei denen Text und Gesang nicht sicher zusammenpassen, behalten die lrclib-Zeiten.

### Podcasts

In der Player-Kachel (Bibliothek → Podcasts) lassen sich Podcasts suchen oder per Spotify-Link öffnen, abonnieren und das Abo beenden. In einem Podcast gibt es „Neueste Folge“, „Alles abspielen“ und „Zufällig abspielen“. Jede Folge zeigt Datum, Länge und Hörfortschritt und startet dort, wo du aufgehört hast (im Menü der Folge auch „Von vorn“ und „Folge merken“). Gemerkte Folgen stehen unter „Gespeicherte Folgen“.

### Durchsagen (TTS, Nachrichten, Radio-Links)

`spotify_flex_app.announce` spielt Ansagen oder Audio-Links synchron über die Spotify-Flex-Lautsprecher (AirPlay 2 über OwnTone). Spotify wird dafür pausiert, die Lautstärken der Lautsprecher werden danach wiederhergestellt. `spotify_flex_app.stop_announcement` bricht ab.

```yaml
action: spotify_flex_app.announce
data:
  group: Wohnzimmer            # optional: Gruppe vorher einschalten
  media:
    - media_content_id: "media-source://tts/tts.piper?message=Guten%20Morgen"
      volume: 35
    - media_content_id: "https://example.org/nachrichten.mp3"
      volume: 50
  wait: true                   # erst zurück, wenn alles gespielt ist
```

Liedtexte kommen von lrclib.net (Titel, Künstler, Album und Dauer werden dorthin gesendet). Die Verzögerung zwischen Spotify und dem Lautsprecher misst die App laufend selbst (Attribut `audio_latency_ms` am Player).

## Voraussetzungen und Grenzen

* Spotify Premium.
* **Music Assistant darf nicht gleichzeitig laufen.** Für AirPlay 2 belegt es dieselben Zeitports 319/320 wie diese App. Beim Start meldet das Protokoll, ob die Ports frei sind.
* HomePods im selben Netz. Falls ein HomePod nicht reagiert: in der Home-App unter *Zuhause-Einstellungen → Lautsprecher und TV* den Zugriff auf „Alle im selben Netzwerk“ stellen.
* Die Web-API läuft über deine eigene Entwickler-App. Spotify-Kontingente und Einschränkungen des Entwicklungsmodus gelten weiter.
* AirPlay hat etwa 2 Sekunden Verzögerung zwischen Tippen und Ton.
