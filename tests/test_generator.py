"""Run without installing Home Assistant: python3 -m unittest discover -s tests."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("generator", Path(__file__).parents[1] / "custom_components/dsj_dashboard/generator.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def entity(eid, **kwargs):
    return {"entity_id": eid, "name": eid, "attributes": {}, **kwargs}


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.areas = [{"area_id": "living", "name": "Woonkamer", "floor_id": "down"}, {"area_id": "bed", "name": "Slaapkamer", "floor_id": "up"}]
        self.floors = [{"floor_id": "down", "name": "Begane grond", "level": 0}, {"floor_id": "up", "name": "Verdieping", "level": 1}]
        self.entities = [entity("light.sofa", device_id="device1"), entity("sensor.temp", area_id="living", device_class="temperature"), entity("lock.door", area_id="living")]
        self.devices = {"device1": {"area_id": "living"}}
        self.prefs = {"hidden": [], "favorites": []}

    def build(self, **kwargs):
        return g.build_dashboard(self.areas, self.floors, kwargs.get("entities", self.entities), self.devices, kwargs.get("prefs", self.prefs), kwargs.get("energy", {}), kwargs.get("options", {}))

    def page(self, result, name):
        return next(v["cards"][0] for v in result["views"] if v["path"] == name)

    def rooms(self, result):
        return self.page(result, "ruimtes")["rooms"]

    def test_device_area_is_inherited(self):
        self.assertEqual(self.rooms(self.build())[0]["lights"], ["light.sofa"])

    def test_entity_area_overrides_device(self):
        self.entities[0]["area_id"] = "bed"
        rooms = self.rooms(self.build())
        self.assertEqual(rooms[1]["lights"], ["light.sofa"])
        self.assertEqual(rooms[0]["lights"], [])

    def test_hidden_entity_removed_from_all_generated_locations(self):
        result = self.build(prefs={"hidden": ["light.sofa"], "favorites": ["light.sofa"]})
        self.assertNotIn("light.sofa", json.dumps(result))

    def test_ha_hidden_disabled_and_diagnostic_entities_are_excluded(self):
        for key, value in [("hidden_by", "user"), ("disabled_by", "integration"), ("entity_category", "diagnostic")]:
            with self.subTest(key=key):
                self.entities[0][key] = value
                self.assertNotIn("light.sofa", json.dumps(self.build()))
                del self.entities[0][key]

    def test_favorite_without_area_is_excluded(self):
        self.entities.append(entity("switch.extra"))
        result = self.build(prefs={"hidden": [], "favorites": ["switch.extra"]})
        self.assertNotIn("switch.extra", json.dumps(result))

    def test_unavailable_entity_stays_present(self):
        self.entities[0]["state"] = "unavailable"
        self.assertIn("light.sofa", json.dumps(self.build()))

    def test_floor_order_and_empty_rooms(self):
        self.areas.reverse()
        self.entities.append(entity("light.bed", area_id="bed"))
        self.assertEqual([r["id"] for r in self.rooms(self.build())], ["living", "bed"])
        self.assertEqual(len(self.rooms(self.build(entities=[]))), 0)

    def test_new_room_and_device_discovered(self):
        before = self.build()
        self.areas.append({"area_id": "garage", "name": "Garage"})
        self.entities.append(entity("cover.garage", area_id="garage"))
        after = self.build()
        self.assertEqual(len(self.rooms(after)), len(self.rooms(before)) + 1)

    def test_temperature_and_humidity_are_classified(self):
        self.entities.append(entity("sensor.hum", area_id="living", device_class="humidity"))
        sensors = self.rooms(self.build())[0]["sensors"]
        self.assertEqual(sensors, {"temperature": "sensor.temp", "humidity": "sensor.hum"})

    def test_security_and_media_without_area_are_excluded(self):
        result = self.build(entities=[entity("camera.outdoor"), entity("media_player.radio")])
        self.assertNotIn("camera.outdoor", json.dumps(result))
        self.assertNotIn("media_player.radio", json.dumps(result))

    def test_energy_uses_ha_preferences_and_conditional_sources(self):
        energy = {"energy_sources": [{"type": "grid"}, {"type": "solar"}], "device_consumption": []}
        result = self.page(self.build(energy=energy), "energie")
        types = [c["type"] for group in result["groups"] for c in group["cards"]]
        self.assertIn("energy-usage-graph", types)
        self.assertIn("energy-solar-graph", types)
        self.assertNotIn("energy-gas-graph", types)
        self.assertNotIn("entity", json.dumps(result["groups"]))
        energy["energy_sources"].append({"type": "gas"})
        self.assertIn("energy-gas-graph", json.dumps(self.page(self.build(energy=energy), "energie")))

    def test_empty_energy_has_setup_message(self):
        self.assertIn("Stel eerst", json.dumps(self.page(self.build(), "energie")))

    def test_scene_uses_turn_on_not_toggle(self):
        card = g.tile(entity("scene.evening"))
        self.assertEqual(card["tap_action"]["perform_action"], "scene.turn_on")

    def test_locks_have_no_one_tap_unlock(self):
        card = g.tile(entity("lock.front"))
        self.assertEqual(card["tap_action"]["action"], "more-info")
        self.assertNotIn("lock.unlock", json.dumps(card))

    def test_only_supported_light_controls(self):
        self.assertNotIn("features", g.tile(entity("light.simple", attributes={"supported_color_modes": ["onoff"]})))
        card = g.tile(entity("light.dimmer", attributes={"supported_color_modes": ["brightness"]}))
        self.assertEqual(card["features"], [{"type": "light-brightness"}])

    def test_separate_installations_have_no_demo_ids(self):
        result = self.build(entities=[entity("light.customer_xyz", area_id="bed")])
        encoded = json.dumps(result)
        self.assertIn("light.customer_xyz", encoded)
        for old in ("light.sofa", "weather.forecast_home", "sensor.solaredge", "person.admin", "dashboard-demo"):
            self.assertNotIn(old, encoded)

    def test_deterministic_and_no_mutation(self):
        before = json.dumps([self.areas, self.entities, self.prefs], sort_keys=True)
        first = self.build()
        self.assertEqual(first, self.build())
        first["views"].clear()
        self.assertEqual(len(self.build()["views"]), 7)
        self.assertEqual(before, json.dumps([self.areas, self.entities, self.prefs], sort_keys=True))

    def test_area_preferred_sensor_is_used_if_visible(self):
        self.entities.append(entity("sensor.preferred", area_id="living", device_class="temperature"))
        self.areas[0]["temperature_entity_id"] = "sensor.preferred"
        self.assertEqual(self.rooms(self.build())[0]["sensors"]["temperature"], "sensor.preferred")
        self.prefs["hidden"] = ["sensor.preferred"]
        self.assertEqual(self.rooms(self.build())[0]["sensors"]["temperature"], "sensor.temp")

    def test_sonos_uses_only_visible_sonos_entities_and_has_fallback(self):
        self.entities.extend([entity("media_player.sonos_a", platform="sonos", area_id="living"), entity("media_player.sonos_b", platform="sonos", area_id="living"), entity("media_player.radio", platform="other", area_id="living")])
        self.prefs["hidden"] = ["media_player.sonos_b"]
        media = self.page(self.build(), "media")
        sonos = media["groups"][0]["cards"][0]
        self.assertEqual(sonos["preferred"]["entities"], ["media_player.sonos_a"])
        self.assertEqual(sonos["fallback"]["type"], "vertical-stack")
        self.assertNotIn("media_player.sonos_b", json.dumps(media))
        self.assertIn("media_player.radio", json.dumps(media))
        native = self.page(self.build(options={"original_cards": False}), "media")
        self.assertNotIn("dsj-optional-card", json.dumps(native))

    def test_lights_overview_contains_groups_only(self):
        self.entities.extend([
            entity("light.group_helper", area_id="living", platform="group"),
            entity("light.group_members", device_id="device1", attributes={"entity_id":["light.sofa"]}),
            entity("light.group_label", area_id="living", labels=["light_group"]),
            entity("light.group_hue", area_id="bed", attributes={"is_hue_group": True}),
            entity("light.unassigned_group", platform="group"),
        ])
        home = self.page(self.build(), "hoofdpagina")
        overview = next(group for group in home["groups"] if group["title"] == "Aanstaande lampen")
        self.assertEqual(set(overview["cards"][0]["entities"]), {"light.group_helper", "light.group_members", "light.group_label", "light.group_hue"})
        self.assertEqual(home["light_summary"], "groups")

    def test_hidden_groups_stay_out_of_lights_overview(self):
        self.entities.extend([entity("light.group1",area_id="living",platform="group"),entity("light.group2",area_id="living",platform="group")])
        self.prefs["hidden"] = ["light.group1"]
        home = self.page(self.build(), "hoofdpagina")
        overview = next(group for group in home["groups"] if group["title"] == "Aanstaande lampen")
        self.assertEqual(overview["cards"][0]["entities"], ["light.group2"])

    def test_individual_lights_still_appear_in_room_popup(self):
        self.assertIn("light.sofa",json.dumps(self.rooms(self.build())[0]["groups"]))
        self.assertNotIn("entity-filter",json.dumps(self.page(self.build(), "hoofdpagina")))

    def test_missing_or_deleted_area_excludes_entity_everywhere(self):
        self.entities.append(entity("climate.orphan", area_id="deleted_area"))
        self.assertNotIn("climate.orphan",json.dumps(self.build()))

    def test_device_assignment_is_sufficient_for_media(self):
        result = self.build(entities=[entity("media_player.radio",device_id="device1")])
        self.assertIn("media_player.radio",json.dumps(self.page(result,"media")))

    def test_label_and_group_names_are_not_guessed(self):
        self.assertFalse(g.is_light_group(entity("light.group_in_name",name="Lichtgroep")))
        self.assertFalse(g.is_light_group(entity("light.single", attributes={"entity_id": "light.other"})))
        self.assertFalse(g.is_light_group(entity("switch.group", labels=["light_group"])))

    def test_theme_selection_is_optional(self):
        self.assertNotIn("theme", self.build()["views"][0])
        self.assertEqual(self.build(options={"theme": "DSJ Border"})["views"][0]["theme"], "DSJ Border")

if __name__ == "__main__":
    unittest.main()
