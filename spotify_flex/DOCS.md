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

## Voraussetzungen und Grenzen

* Spotify Premium.
* HomePods im selben Netz. Falls ein HomePod nicht reagiert: in der Home-App unter *Zuhause-Einstellungen → Lautsprecher und TV* den Zugriff auf „Alle im selben Netzwerk“ stellen.
* Die Web-API läuft über deine eigene Entwickler-App. Spotify-Kontingente und Einschränkungen des Entwicklungsmodus gelten weiter.
* AirPlay hat etwa 2 Sekunden Verzögerung zwischen Tippen und Ton.
