"""Spotify Flex Player: Home Assistant entities for the Spotify Flex app."""
from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .client import FlexClient
from .const import CARD_URL, CONF_TOKEN, DOMAIN
from .coordinator import FlexCoordinator
from .services import async_setup_services

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SELECT]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the player card and register the card services."""
    from homeassistant.components.http import StaticPathConfig

    card = Path(__file__).parent / "www" / "spotify-flex-flow-card.js"
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(card), False)])
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = FlexClient(async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT],
                        entry.data[CONF_TOKEN])
    coordinator = FlexCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    coordinator.start_push()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        await entry.runtime_data.stop_push()
    return ok
