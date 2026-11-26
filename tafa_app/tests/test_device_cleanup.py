"""TAFA deletion must never remove unrelated Home Assistant entities."""
import ast
import types
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[2] /
          "custom_components/tablet_assist_for_alexa/device_cleanup.py")


class RegistryEntry:
    def __init__(self, entity_id, unique_id, platform):
        self.entity_id, self.unique_id, self.platform = entity_id, unique_id, platform


class FakeEntityRegistry:
    def __init__(self, entries):
        self.entries = list(entries)
        self.removed = []

    def async_remove(self, entity_id):
        self.removed.append(entity_id)
        self.entries = [e for e in self.entries if e.entity_id != entity_id]


class FakeDeviceRegistry:
    def __init__(self, identifier, config_entries):
        self.device = types.SimpleNamespace(id="device-1", config_entries=config_entries)
        self.identifier = ("tablet_assist_for_alexa", identifier)
        self.removed = []

    def async_get_device(self, identifiers):
        return self.device if self.identifier in identifiers else None

    def async_remove_device(self, device_id):
        self.removed.append(device_id)


def load_cleanup(fake_er, fake_dr):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    methods = [node for node in tree.body
               if isinstance(node, ast.FunctionDef)
               and node.name in ("_cleanup", "cleanup_tablet", "cleanup_room")]
    env = {"DOMAIN": "tablet_assist_for_alexa",
           "er": types.SimpleNamespace(
               async_get=lambda _: fake_er,
               async_entries_for_device=lambda reg, device_id: list(reg.entries)),
           "dr": types.SimpleNamespace(async_get=lambda _: fake_dr)}
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=methods, type_ignores=[])), str(SOURCE), "exec"), env)
    return env


class DeleteRegistryTest(unittest.TestCase):
    def test_only_tafa_owned_tablet_entities_are_removed(self):
        tablet = "a" * 32
        entity_registry = FakeEntityRegistry([
            RegistryEntry("sensor.tafa", "tafa_" + tablet + "_battery",
                          "tablet_assist_for_alexa"),
            RegistryEntry("sensor.other", "tafa_" + tablet + "_weather",
                          "unrelated_platform"),
        ])
        device_registry = FakeDeviceRegistry(tablet, {"tafa-entry"})
        env = load_cleanup(entity_registry, device_registry)
        env["cleanup_tablet"](object(), tablet)
        self.assertEqual(entity_registry.removed, ["sensor.tafa"])
        self.assertEqual(device_registry.removed, [])
        self.assertEqual(len(entity_registry.entries), 1)

    def test_tablet_device_is_removed_when_no_entities_remain(self):
        tablet = "b" * 32
        entity_registry = FakeEntityRegistry([
            RegistryEntry("number.tafa", "tafa_" + tablet + "_brightness",
                          "tablet_assist_for_alexa")])
        device_registry = FakeDeviceRegistry(tablet, {"tafa-entry"})
        env = load_cleanup(entity_registry, device_registry)
        env["cleanup_tablet"](object(), tablet)
        self.assertEqual(device_registry.removed, ["device-1"])

    def test_room_cleanup_releases_id_for_recreation(self):
        entry_id = "123entry"
        room = "buero"
        identity = entry_id + "_room_" + room
        entity_registry = FakeEntityRegistry([
            RegistryEntry("camera.tafa", identity + "_camera",
                          "tablet_assist_for_alexa"),
            RegistryEntry("binary_sensor.tafa", identity + "_motion",
                          "tablet_assist_for_alexa")])
        device_registry = FakeDeviceRegistry(identity, {"tafa-entry"})
        env = load_cleanup(entity_registry, device_registry)
        hub = types.SimpleNamespace(entry=types.SimpleNamespace(entry_id=entry_id),
                                    forgotten=[])
        hub.forget_room = lambda rid: hub.forgotten.append(rid)
        hass = types.SimpleNamespace(data={
            "tablet_assist_for_alexa": {"room_cameras": hub}})
        env["cleanup_room"](hass, room)
        self.assertCountEqual(entity_registry.removed,
                              ["camera.tafa", "binary_sensor.tafa"])
        self.assertEqual(hub.forgotten, [room])
        self.assertEqual(device_registry.removed, ["device-1"])


if __name__ == "__main__":
    unittest.main()
