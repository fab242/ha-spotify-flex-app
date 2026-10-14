"""Select entity: switch to a saved speaker group (or switch all speakers off)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import OFF_OPTION
from .coordinator import FlexCoordinator
from .media_player import main_device


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([FlexGroupSelect(entry.runtime_data)])


class FlexGroupSelect(CoordinatorEntity[FlexCoordinator], SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "group"
    _attr_icon = "mdi:speaker-multiple"

    def __init__(self, coordinator: FlexCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "group"
        self._attr_device_info = main_device(coordinator)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.coordinator.async_update_listeners()  # player lists this entity as group_entity

    @property
    def options(self) -> list[str]:
        return [OFF_OPTION] + [g["name"] for g in self.coordinator.groups]

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.selected_ids():
            return OFF_OPTION
        active = (self.coordinator.data or {}).get("active_group")
        return next((g["name"] for g in self.coordinator.groups if g["id"] == active), None)

    async def async_select_option(self, option: str) -> None:
        if option == OFF_OPTION:
            await self.coordinator.command("POST", "/api/speakers", {"speakers": []})
            return
        group = next((g for g in self.coordinator.groups if g["name"] == option), None)
        if not group:
            raise ServiceValidationError(f"Unbekannte Gruppe: {option}")
        await self.coordinator.command("POST", f"/api/groups/{group['id']}/activate", {})
