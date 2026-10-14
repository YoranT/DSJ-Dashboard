"""Deterministic dashboard generation, independent of Home Assistant imports."""
from copy import deepcopy

PAGES = [
    ("hoofdpagina", "Home", "mdi:home"),
    ("ruimtes", "Ruimtes", "mdi:floor-plan"),
    ("media", "Media", "mdi:television-speaker"),
    ("energie", "Energie", "mdi:lightning-bolt"),
    ("klimaat", "Klimaat", "mdi:thermometer"),
    ("beveiliging", "Beveiliging", "mdi:security"),
    ("instellingen", "Instellingen", "mdi:cog"),
]
DOMAINS = {
    "light", "switch", "scene", "script", "climate", "fan", "cover", "vacuum",
    "media_player", "sensor", "binary_sensor", "lock", "alarm_control_panel",
    "camera", "weather", "humidifier", "water_heater", "input_boolean", "button",
    "input_select", "select", "number", "input_number", "siren",
}
SECURITY_CLASSES = {"door", "window", "opening", "motion", "occupancy", "smoke", "gas", "moisture", "tamper", "safety"}
CLIMATE_CLASSES = {"temperature", "humidity", "carbon_dioxide", "volatile_organic_compounds"}


def domain(entity):
    return entity["entity_id"].split(".", 1)[0]


def resolve_area(entity, devices):
    """Explicit entity area takes precedence over the device's area."""
    return entity.get("area_id") or devices.get(entity.get("device_id"), {}).get("area_id")


def visible(entity, hidden):
    return (domain(entity) in DOMAINS and not entity.get("disabled_by")
            and not entity.get("hidden_by") and entity["entity_id"] not in hidden
            and not entity.get("entity_category"))


def is_light_group(entity):
    """Use group metadata or an explicit label; never guess from names."""
    if domain(entity) != "light":
        return False
    attrs = entity.get("attributes", {})
    members = attrs.get("entity_id", [])
    has_light_members = isinstance(members, (list, tuple)) and bool(members) and all(isinstance(eid, str) and eid.startswith("light.") for eid in members)
    return bool(entity.get("platform") == "group" or has_light_members
                or attrs.get("is_hue_group") is True
                or set(entity.get("labels", [])) & {"light_group", "dsj_light_group"})


def category(entity):
    d, dc = domain(entity), entity.get("device_class")
    if d == "light":
        return "Verlichting"
    if d == "scene":
        return "Scènes"
    if d == "media_player":
        return "Media"
    if d in {"climate", "fan", "humidifier", "water_heater"} or (d == "sensor" and dc in CLIMATE_CLASSES):
        return "Klimaat"
    if d in {"lock", "alarm_control_panel", "camera", "siren"} or (d == "binary_sensor" and dc in SECURITY_CLASSES):
        return "Beveiliging"
    if d == "cover":
        return "Zonwering en gordijnen"
    return "Overige apparaten"


def tile(entity):
    """Expose controls only where capabilities are known; more-info is the fallback."""
    eid, d = entity["entity_id"], domain(entity)
    attrs = entity.get("attributes", {})
    features = []
    if d == "camera":
        return {"type": "picture-entity", "entity": eid, "camera_view": "auto", "show_name": True, "show_state": False}
    if d == "media_player":
        return {"type": "media-control", "entity": eid}
    if d == "alarm_control_panel":
        return {"type": "alarm-panel", "entity": eid}
    if d == "light":
        modes = set(attrs.get("supported_color_modes", []))
        if modes - {"onoff", "unknown"}:
            features.append({"type": "light-brightness"})
        if "color_temp" in modes:
            features.append({"type": "light-color-temp"})
    if d == "climate":
        if int(attrs.get("supported_features", 0)) & 3:
            features.append({"type": "target-temperature"})
        if attrs.get("hvac_modes"):
            features.append({"type": "climate-hvac-modes"})
    if d == "cover" and int(attrs.get("supported_features", 0)) & 3:
        features.append({"type": "cover-open-close"})
    result = {"type": "tile", "entity": eid, "vertical": False, "tap_action": {"action": "more-info"}}
    if d in {"scene", "script", "button"}:
        service = {"scene": "scene.turn_on", "script": "script.turn_on", "button": "button.press"}[d]
        result["tap_action"] = {"action": "perform-action", "perform_action": service, "target": {"entity_id": eid}}
    if d in {"lock", "siren"}:
        # No one-tap unlock/disarm; use HA's own more-info controls and PIN handling.
        result["icon_tap_action"] = {"action": "more-info"}
    if features:
        result.update(features=features, features_position="bottom")
    return result


def group_entities(entities):
    titles = ["Verlichting", "Scènes", "Media", "Klimaat", "Zonwering en gordijnen", "Beveiliging", "Overige apparaten"]
    return [{"title": title, "cards": [tile(e) for e in entities if category(e) == title]}
            for title in titles if any(category(e) == title for e in entities)]


def energy_groups(prefs):
    sources = prefs.get("energy_sources", [])
    kinds = {s["type"] for s in sources}
    if not kinds and not prefs.get("device_consumption"):
        return [{"title": "Energie", "cards": [{"type": "markdown", "content": "Stel eerst de energiemeters in via **Instellingen → Dashboards → Energie**. Dit dashboard gebruikt daarna dezelfde gegevens."}]}]
    groups = [{"title": "Overzicht", "cards": [{"type": "energy-date-selection"}, {"type": "energy-distribution", "link_dashboard": True}]}]
    if any(source.get("stat_rate") or source.get("power_config") for source in sources):
        groups.append({"title": "Actueel vermogen", "cards": [{"type": "power-sources-graph"}, {"type": "power-sankey"}]})
    graphs = []
    for kind, card in [("grid", "energy-usage-graph"), ("solar", "energy-solar-graph"), ("gas", "energy-gas-graph"), ("water", "energy-water-graph")]:
        if kind in kinds:
            graphs.append({"type": card})
    if prefs.get("device_consumption"):
        graphs.append({"type": "energy-devices-graph"})
    if graphs:
        groups.append({"title": "Verbruik en opwek", "cards": graphs})
    groups.append({"title": "Kosten en bronnen", "cards": [{"type": "energy-sources-table"}]})
    return groups


def build_dashboard(areas, floors, entities, devices, preferences, energy, options, url_path="dsj-dashboard"):
    """Generate a fresh config; never modify input registries or customer settings."""
    hidden = set(preferences.get("hidden", []))
    area_ids = {area["area_id"] for area in areas}
    active = sorted((e for e in entities if visible(e, hidden) and resolve_area(e, devices) in area_ids), key=lambda e: (e.get("name", e["entity_id"]).casefold(), e["entity_id"]))
    by_id = {e["entity_id"]: e for e in active}
    floor_map = {f["floor_id"]: f for f in floors}
    rooms = []
    def room_sort(a):
        floor = floor_map.get(a.get("floor_id"), {})
        return (floor.get("level") if floor.get("level") is not None else 999, floor.get("name", "").casefold(), a["name"].casefold(), a["area_id"])
    for area in sorted(areas, key=room_sort):
        room_entities = [e for e in active if resolve_area(e, devices) == area["area_id"]]
        if not room_entities:
            continue
        floor = floor_map.get(area.get("floor_id"), {})
        sensors = {dc: next((e["entity_id"] for e in room_entities if domain(e) == "sensor" and e.get("device_class") == dc), None) for dc in ("temperature", "humidity")}
        for dc in ("temperature", "humidity"):
            preferred = area.get(f"{dc}_entity_id")
            if preferred in by_id:
                sensors[dc] = preferred
        rooms.append({"id": area["area_id"], "name": area["name"], "icon": area.get("icon") or "mdi:floor-plan", "floor": floor.get("name") or "Ruimtes", "lights": [e["entity_id"] for e in room_entities if domain(e) == "light"], "sensors": sensors, "groups": group_entities(room_entities)})
    favorites = [by_id[eid] for eid in preferences.get("favorites", []) if eid in by_id]
    home = []
    if favorites:
        home.append({"title": "Favorieten", "cards": [tile(e) for e in favorites]})
    lights = [e for e in active if is_light_group(e)]
    if lights:
        home.append({"title": "Aanstaande lampen", "cards": [{"type": "entity-filter", "entities": [e["entity_id"] for e in lights], "state_filter": ["on"], "show_empty": False, "card": {"type": "entities", "show_header_toggle": False}}]})
    weather = next((e for e in active if domain(e) == "weather"), None)
    if weather:
        home.append({"title": "Weer", "cards": [{"type": "weather-forecast", "entity": weather["entity_id"], "forecast_type": "daily"}]})
    if not home:
        home.append({"title": "Welkom", "cards": [{"type": "markdown", "content": "Koppel apparaten aan ruimtes in Home Assistant. Kies daarna bij **Instellingen** je favorieten."}]})
    room_groups = []
    for room in rooms:
        if not room_groups or room_groups[-1]["title"] != room["floor"]:
            room_groups.append({"title": room["floor"], "cards": []})
        room_groups[-1]["cards"].append({"type": "custom:dsj-room-card", "room": room, "original_cards": options.get("original_cards", True)})
    media, climate, security = [], [], []
    # Only entities assigned to a current area enter customer-facing pages.
    area_names = {a["area_id"]: a["name"] for a in areas}
    for destination, wanted in [(media, "Media"), (climate, "Klimaat"), (security, "Beveiliging")]:
        buckets = {}
        for e in active:
            if category(e) == wanted:
                name = area_names.get(resolve_area(e, devices), "Zonder ruimte")
                buckets.setdefault(name, []).append(tile(e))
        destination.extend({"title": name, "cards": cards} for name, cards in buckets.items())
    sonos = [e for e in active if domain(e) == "media_player" and e.get("platform") == "sonos"]
    if sonos and options.get("original_cards", True):
        sonos_ids = {e["entity_id"] for e in sonos}
        media = [{**group, "cards": [c for c in group["cards"] if c.get("entity") not in sonos_ids]} for group in media]
        media = [group for group in media if group["cards"]]
        media.insert(0, {"title": "Sonos", "cards": [{"type": "custom:dsj-optional-card", "element": "sonos-card", "preferred": {"type": "custom:sonos-card", "entityId": sonos[0]["entity_id"], "entities": [e["entity_id"] for e in sonos]}, "fallback": {"type": "vertical-stack", "cards": [tile(e) for e in sonos]}}]})
    content = {"hoofdpagina": home, "ruimtes": room_groups, "media": media, "energie": energy_groups(energy), "klimaat": climate, "beveiliging": security, "instellingen": []}
    views = []
    for path, title, icon in PAGES:
        page = {"type": "custom:dsj-page-card", "page": path, "title": title, "url_path": url_path, "accent": options.get("accent", "#b98c27"), "groups": content[path], "rooms": rooms if path == "ruimtes" else [], "original_cards": options.get("original_cards", True), "light_summary": "groups"}
        view = {"title": title, "path": path, "icon": icon, "type": "panel", "cards": [page]}
        if options.get("theme"):
            view["theme"] = options["theme"]
        views.append(view)
    return deepcopy({"title": "De Slimme Jongens", "views": views})
