"""Constants shared by the Spotify Flex app backend."""

VERSION = "1.7.4"

API_BASE = "https://api.spotify.com/v1"
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
REDIRECT_URI = "http://127.0.0.1:8765/callback"

SCOPES = (
    "user-read-private", "user-read-email", "user-read-playback-state",
    "user-read-currently-playing", "user-modify-playback-state", "user-read-playback-position",
    "user-read-recently-played", "user-top-read", "user-library-read", "user-library-modify",
    "user-follow-read", "user-follow-modify", "playlist-read-private", "playlist-read-collaborative",
    "playlist-modify-private", "playlist-modify-public", "ugc-image-upload",
)

PAGE_LIMIT = 50
SEARCH_LIMIT_MAX = 10
ARTIST_ALBUMS_MAX = 10
LIBRARY_URIS_MAX = 40
PLAYLIST_ITEMS_MAX = 100

LIBRESPOT_URL = "http://127.0.0.1:3678"
OWNTONE_URL = "http://127.0.0.1:3689"
OPTIONS_FILE = "/data/options.json"
TOKEN_FILE = "/data/web_token.json"
STATE_FILE = "/data/state.json"
LIBRESPOT_STATE = "/config/go-librespot/state.json"
LIBRESPOT_CONFIG = "/config/go-librespot/config.yml"
LIBRESPOT_SERVICE = "/run/service/svc-golibrespot"
EQ_FILE = "/data/eq.json"
EQ_CONTROL = "/run/flex/eq.conf"
INGRESS_PORT = 8099
GROUPS_FILE = "/data/groups.json"
API_TOKEN_FILE = "/data/api_token"
INTEGRATION_DOMAIN = "spotify_flex_app"
INTEGRATION_SRC = "/opt/flex/integration/spotify_flex_app"
HA_CUSTOM_COMPONENTS = "/homeassistant/custom_components"
SUPERVISOR_URL = "http://supervisor"
