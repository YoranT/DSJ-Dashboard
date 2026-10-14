"""DSJ's automatically generated Home Assistant dashboard."""
import asyncio
from copy import deepcopy
from pathlib import Path
import probatio as vol
from homeassistant.components import frontend, websocket_api
from homeassistant.components.energy.data import async_get_manager
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.dashboard import LovelaceConfig
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_STATE_CHANGED
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er, floor_registry as fr
from homeassistant.helpers.json import cached_json_fragment
from homeassistant.helpers.storage import Store
from .const import DEFAULTS, DOMAIN, MODULE_URL, URL_PATH
from .generator import DOMAINS, build_dashboard, resolve_area
from .resource_registration import ensure_lovelace_resource


class DSJLovelace(LovelaceConfig):
    """Read-only generated configuration; customer dashboards are never overwritten."""
    def __init__(self, manager):
        super().__init__(manager.hass, URL_PATH, {"title": "De Slimme Jongens", "icon": "mdi:home-lightning-bolt", "show_in_sidebar": True, "require_admin": False, "mode": "yaml"})
        self.manager = manager
        self._json = None

    @property
    def mode(self):
        return "yaml"

    async def async_get_info(self):
        return {"mode": self.mode, "views": 7}

    async def async_load(self, force):
        return self.manager.build()

    async def async_json(self, force):
        if force or self._json is None:
            self._json = cached_json_fragment(self.manager.build())
        return self._json

    @callback
    def invalidate(self):
        self._json = None
        self._config_updated()


class DSJManager:
    def __init__(self, hass, entry, energy):
        self.hass, self.entry, self.energy = hass, entry, energy
        self.store = Store(hass, 1, DOMAIN)
        self.preferences = {"hidden": [], "favorites": []}
        self.lock = asyncio.Lock()
        self.dashboard = DSJLovelace(self)
        self.unsubs = []
        self.timer = None
        self.active = True

    def snapshot(self):
        areas = [{"area_id": a.id, "name": a.name, "floor_id": a.floor_id, "icon": a.icon, "temperature_entity_id": a.temperature_entity_id, "humidity_entity_id": a.humidity_entity_id} for a in ar.async_get(self.hass).async_list_areas()]
        floors = [{"floor_id": f.floor_id, "name": f.name, "level": f.level} for f in fr.async_get(self.hass).async_list_floors()]
        devices = {d.id: {"area_id": d.area_id} for d in dr.async_get(self.hass).devices}
        states = {s.entity_id: s for s in self.hass.states.async_all()}
        registry = er.async_get(self.hass)
        entities = []
        for eid in sorted(set(states) | set(registry.entities)):
            record, state = registry.async_get(eid), states.get(eid)
            attributes = dict(state.attributes) if state else {}
            entities.append({
                "entity_id": eid,
                "name": (record.name if record else None) or attributes.get("friendly_name") or (record.original_name if record else None) or eid,
                "area_id": record.area_id if record else None,
                "device_id": record.device_id if record else None,
                "platform": record.platform if record else None,
                "labels": sorted(record.labels) if record else [],
                "hidden_by": str(record.hidden_by) if record and record.hidden_by else None,
                "disabled_by": str(record.disabled_by) if record and record.disabled_by else None,
                "entity_category": str(record.entity_category) if record and record.entity_category else None,
                "device_class": attributes.get("device_class") or ((record.device_class or record.original_device_class) if record else None),
                "attributes": attributes,
            })
        return areas, floors, entities, devices

    def build(self):
        return build_dashboard(*self.snapshot(), self.preferences, self.energy.data or {}, {**DEFAULTS, **self.entry.options}, url_path=URL_PATH)

    def inventory(self):
        areas, _, entities, devices = self.snapshot()
        area_names = {a["area_id"]: a["name"] for a in areas}
        result = []
        for e in entities:
            if e["entity_id"].split(".", 1)[0] not in DOMAINS:
                continue
            reason = ""
            if e["disabled_by"]:
                reason = "Uitgeschakeld in Home Assistant"
            elif e["hidden_by"]:
                reason = "Verborgen in Home Assistant"
            elif e["entity_category"]:
                reason = "Configuratie- of diagnose-entiteit"
            elif resolve_area(e, devices) not in area_names:
                reason = "Geen ruimte toegewezen — niet getoond"
            result.append({"entity_id": e["entity_id"], "name": e["name"], "area": area_names.get(resolve_area(e, devices), "Zonder ruimte"), "hidden": e["entity_id"] in self.preferences["hidden"], "favorite": e["entity_id"] in self.preferences["favorites"], "reason": reason})
        return result

    async def change(self, entity_id, operation, value):
        if not self.hass.states.get(entity_id) and not er.async_get(self.hass).async_get(entity_id):
            raise ValueError("Entiteit bestaat niet meer")
        key = "hidden" if operation == "hide" else "favorites"
        async with self.lock:
            changed = deepcopy(self.preferences)
            values = changed[key]
            if value and entity_id not in values:
                values.append(entity_id)
            elif not value and entity_id in values:
                values.remove(entity_id)
            await self.store.async_save(changed)
            self.preferences = changed
        self.schedule()

    async def rename(self, old, new):
        async with self.lock:
            changed = {key: list(dict.fromkeys(new if eid == old else eid for eid in values)) for key, values in self.preferences.items()}
            if changed != self.preferences:
                await self.store.async_save(changed)
                self.preferences = changed
        self.schedule()

    @callback
    def schedule(self, event=None):
        if not self.active:
            return
        if event and event.data.get("old_entity_id"):
            self.hass.async_create_task(self.rename(event.data["old_entity_id"], event.data["entity_id"]))
            return
        if self.timer:
            self.timer.cancel()
        self.timer = self.hass.loop.call_later(0.5, self.refresh)

    @callback
    def refresh(self):
        self.timer = None
        if self.active:
            self.dashboard.invalidate()

    @callback
    def state_changed(self, event):
        old, new = event.data.get("old_state"), event.data.get("new_state")
        keys = ("friendly_name", "device_class", "supported_features", "supported_color_modes", "hvac_modes", "entity_id", "is_hue_group")
        if old is None or new is None or any(old.attributes.get(k) != new.attributes.get(k) for k in keys):
            self.schedule()


async def async_setup(hass, config):
    hass.data[DOMAIN] = {"manager": None}
    await hass.http.async_register_static_paths([StaticPathConfig("/dsj_dashboard", str(Path(__file__).parent / "frontend"), True)])
    await ensure_lovelace_resource(hass.data[LOVELACE_DATA].resources, MODULE_URL)
    frontend.add_extra_js_url(hass, MODULE_URL)
    websocket_api.async_register_command(hass, ws_inventory)
    websocket_api.async_register_command(hass, ws_change)
    energy = await async_get_manager(hass)
    async def energy_changed():
        if manager := hass.data[DOMAIN].get("manager"):
            manager.schedule()
    # This public API has no unsubscribe. Register only once per HA process;
    # dispatch through the currently loaded manager to avoid reload listener leaks.
    energy.async_listen_updates(energy_changed)
    return True


async def async_setup_entry(hass, entry):
    lovelace = hass.data[LOVELACE_DATA]
    if URL_PATH in lovelace.dashboards or frontend.async_panel_exists(hass, URL_PATH):
        raise ConfigEntryError(f"Dashboard URL /{URL_PATH} is already in use")
    manager = DSJManager(hass, entry, await async_get_manager(hass))
    saved = await manager.store.async_load() or {}
    manager.preferences = {key: list(dict.fromkeys(saved.get(key, []))) for key in ("hidden", "favorites")}
    hass.data[DOMAIN]["manager"] = manager
    lovelace.dashboards[URL_PATH] = manager.dashboard
    frontend.async_register_built_in_panel(hass, "lovelace", sidebar_title="De Slimme Jongens", sidebar_icon="mdi:home-lightning-bolt", frontend_url_path=URL_PATH, config={"mode": "yaml"}, require_admin=False)
    for event in (ar.EVENT_AREA_REGISTRY_UPDATED, dr.EVENT_DEVICE_REGISTRY_UPDATED, er.EVENT_ENTITY_REGISTRY_UPDATED, fr.EVENT_FLOOR_REGISTRY_UPDATED):
        manager.unsubs.append(hass.bus.async_listen(event, manager.schedule))
    manager.unsubs.append(hass.bus.async_listen(EVENT_STATE_CHANGED, manager.state_changed))
    manager.unsubs.append(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, manager.schedule))
    entry.async_on_unload(entry.add_update_listener(async_options_updated))
    return True


async def async_options_updated(hass, entry):
    if manager := hass.data[DOMAIN].get("manager"):
        manager.schedule()


async def async_unload_entry(hass, entry):
    manager = hass.data[DOMAIN].get("manager")
    if manager:
        manager.active = False
        for unsub in manager.unsubs:
            unsub()
        if manager.timer:
            manager.timer.cancel()
        hass.data[LOVELACE_DATA].dashboards.pop(URL_PATH, None)
        frontend.async_remove_panel(hass, URL_PATH)
        hass.data[DOMAIN]["manager"] = None
    return True


async def async_remove_entry(hass, entry):
    await Store(hass, 1, DOMAIN).async_remove()


@websocket_api.require_admin
@websocket_api.websocket_command({"type": "dsj_dashboard/inventory"})
@websocket_api.async_response
async def ws_inventory(hass, connection, msg):
    if manager := hass.data[DOMAIN].get("manager"):
        connection.send_result(msg["id"], manager.inventory())
    else:
        connection.send_error(msg["id"], "not_loaded", "DSJ dashboard is niet geladen")


@websocket_api.require_admin
@websocket_api.websocket_command({"type": "dsj_dashboard/change", vol.Required("entity_id"): str, vol.Required("operation"): vol.In(["hide", "favorite"]), vol.Required("value"): bool})
@websocket_api.async_response
async def ws_change(hass, connection, msg):
    manager = hass.data[DOMAIN].get("manager")
    if not manager:
        connection.send_error(msg["id"], "not_loaded", "DSJ dashboard is niet geladen")
        return
    try:
        await manager.change(msg["entity_id"], msg["operation"], msg["value"])
    except ValueError as error:
        connection.send_error(msg["id"], "invalid_entity", str(error))
        return
    connection.send_result(msg["id"], {"saved": True})
