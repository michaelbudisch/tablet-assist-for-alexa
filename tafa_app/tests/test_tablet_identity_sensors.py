"""Unit tests for native TAFA Tabletname and Gerätekennung sensors."""
import ast
import datetime
import pathlib
import time
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SENSOR = ROOT / "custom_components" / "tablet_assist_for_alexa" / "sensor.py"
MIXIN = ROOT / "custom_components" / "tablet_assist_for_alexa" / "tablet_entities.py"

class FakeTabletMixin:
    def __init__(self, controller, device_id, key, label):
        self.controller = controller
        self.device_id = device_id
        self.key = key
        self._attr_unique_id = "tafa_" + device_id + "_" + key
        self._attr_name = label

class FakeSensorEntity:
    pass

class FakeSensorClass:
    BATTERY = "battery"
    TIMESTAMP = "timestamp"

def sensor_class_and_keys():
    tree = ast.parse(SENSOR.read_text(encoding="utf-8"))
    source_nodes = [
        n for n in tree.body
        if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SENSORS"
                                                   for t in n.targets))
        or (isinstance(n, ast.ClassDef) and n.name == "TabletSensor")
    ]
    env = {"TabletMixin": FakeTabletMixin, "SensorEntity": FakeSensorEntity,
           "SensorDeviceClass": FakeSensorClass, "datetime": datetime.datetime,
           "timezone": datetime.timezone, "time": time}
    exec(compile(ast.fix_missing_locations(ast.Module(body=source_nodes, type_ignores=[])),
                 str(SENSOR), "exec"), env)
    return env["TabletSensor"], env["SENSORS"]

class TabletIdentitySensorTests(unittest.TestCase):
    def setUp(self):
        self.sensor, self.keys = sensor_class_and_keys()
        self.first, self.second = "a"*32, "b"*32
        self.controller = types.SimpleNamespace(
            devices={
                self.first: {"device_id": self.first, "room": "Büro Tablet"},
                self.second: {"device_id": self.second, "room": "Sofa Tablet"},
            }, telemetry={},
        )

    def test_new_entities_are_in_the_default_sensor_collection(self):
        self.assertEqual(self.keys["device_name"][0], "Tabletname")
        self.assertEqual(self.keys["device_id"][0], "Gerätekennung")
        # The integration uses this same SENSORS list for every enrolled device.
        self.assertIn("for key in SENSORS", SENSOR.read_text(encoding="utf-8"))
        source = MIXIN.read_text(encoding="utf-8")
        self.assertIn('self._attr_unique_id = "tafa_" + device_id + "_" + key', source)

    def test_value_and_unique_id_are_separate_per_tablet(self):
        first_name = self.sensor(self.controller, self.first, "device_name")
        first_id = self.sensor(self.controller, self.first, "device_id")
        second_name = self.sensor(self.controller, self.second, "device_name")
        second_id = self.sensor(self.controller, self.second, "device_id")
        self.assertEqual(first_name.native_value, "Büro Tablet")
        self.assertEqual(first_id.native_value, self.first)
        self.assertEqual(second_name.native_value, "Sofa Tablet")
        self.assertEqual(second_id.native_value, self.second)
        self.assertEqual(len({s._attr_unique_id for s in
                              (first_name, first_id, second_name, second_id)}), 4)

    def test_rename_updates_value_without_changing_identity_or_unique_id(self):
        name = self.sensor(self.controller, self.first, "device_name")
        identifier = self.sensor(self.controller, self.first, "device_id")
        unique = name._attr_unique_id
        self.controller.devices[self.first]["room"] = "Wohnzimmer Tablet 2"
        self.assertEqual(name.native_value, "Wohnzimmer Tablet 2")
        self.assertEqual(name._attr_unique_id, unique)
        self.assertEqual(identifier.native_value, self.first)
        self.assertEqual(name.native_value, name.native_value.strip())

    def test_metadata_available_without_online_telemetry(self):
        self.controller.telemetry.clear()
        name = self.sensor(self.controller, self.first, "device_name")
        ident = self.sensor(self.controller, self.first, "device_id")
        self.assertEqual(name.native_value, "Büro Tablet")
        self.assertEqual(ident.native_value, self.first)
        self.controller.devices[self.first]["room"] = ""
        self.assertEqual(name.native_value, "TAFA Tablet")

if __name__ == "__main__":
    unittest.main()
