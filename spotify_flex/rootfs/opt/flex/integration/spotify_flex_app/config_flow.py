"""Config flow: set up automatically from the Spotify Flex app (Supervisor discovery)."""
from __future__ import annotations

from typing import Any

try:
    import probatio as vol
except ImportError:  # HA < 2026.x
    import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from homeassistant.helpers.service_info.hassio import HassioServiceInfo
except ImportError:  # older HA
    from homeassistant.components.hassio import HassioServiceInfo

from .client import FlexAuthError, FlexClient, FlexError
from .const import CONF_TOKEN, DEFAULT_HOST, DEFAULT_PORT, DOMAIN

TITLE = "Spotify Flex"


class FlexConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, Any] | None = None

    async def _check(self, data: dict) -> str | None:
        client = FlexClient(async_get_clientsession(self.hass), data[CONF_HOST], data[CONF_PORT],
                            data[CONF_TOKEN])
        try:
            await client.state()
        except FlexAuthError:
            return "invalid_auth"
        except FlexError:
            return "cannot_connect"
        return None

    async def async_step_hassio(self, discovery_info: HassioServiceInfo) -> ConfigFlowResult:
        cfg = discovery_info.config or {}
        data = {CONF_HOST: cfg.get("host", DEFAULT_HOST), CONF_PORT: int(cfg.get("port", DEFAULT_PORT)),
                CONF_TOKEN: cfg.get("token", "")}
        await self.async_set_unique_id(DOMAIN)
        # the token may change (app reinstalled) -> keep the entry, update its data
        self._abort_if_unique_id_configured(updates=data)
        self._discovered = data
        return await self.async_step_hassio_confirm()

    async def async_step_hassio_confirm(self, user_input: dict | None = None) -> ConfigFlowResult:
        assert self._discovered is not None
        if user_input is not None:
            error = await self._check(self._discovered)
            if error:
                return self.async_abort(reason=error)
            return self.async_create_entry(title=TITLE, data=self._discovered)
        self._set_confirm_only()
        return self.async_show_form(step_id="hassio_confirm")

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured(updates=user_input)
            error = await self._check(user_input)
            if not error:
                return self.async_create_entry(title=TITLE, data=user_input)
            errors["base"] = error
        schema = vol.Schema({
            vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_TOKEN): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict | None = None) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = dict(entry.data, **user_input)
            error = await self._check(data)
            if not error:
                return self.async_update_reload_and_abort(entry, data=data)
            errors["base"] = error
        return self.async_show_form(step_id="reauth_confirm",
                                    data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}), errors=errors)
