"""Camera coexistence and single TAFA-tablet identity contracts."""
import ast
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_components/tablet_assist_for_alexa"
BUNDLE = ROOT / "tafa_app/bundle/tablet_assist_for_alexa"


class MigrationContract(unittest.TestCase):
    def test_namespaced_endpoints_and_same_tablet_registry_device(self):
        init = (CUSTOM / "__init__.py").read_text()
        self.assertIn('await setup_relay_camera(hass, entry)', init)
        self.assertIn('active_platforms = PLATFORMS', init)
        self.assertNotIn('if not legacy_present:', init)
        single = (CUSTOM / "relay/relay_camera.py").read_text()
        self.assertIn('API = "/api/tablet_assist_for_alexa/camera"', single)
        self.assertNotIn('API = "/api/jarvis_echo_relay"', single)
        room = (CUSTOM / "relay/relay_room_camera.py").read_text()
        self.assertIn('identifiers={(DOMAIN, identifier)}', room)
        self.assertIn('self.enrolled_device_id(room)', room)
        self.assertIn('name="TAFA · " + device.get("room", room)', room)
        self.assertIn('camera_enabled', (CUSTOM / "relay/relay_room_camera_store.py").read_text())
        for path in ["__init__.py","device_admin_ws.py","relay/relay_camera.py",
                     "relay/relay_room_camera.py","relay/relay_vision.py"]:
            self.assertEqual((CUSTOM / path).read_text(),(BUNDLE / path).read_text())

    def test_administrator_needs_explicit_pairing(self):
        source = (CUSTOM / "device_admin_ws.py").read_text()
        self.assertIn('if action == "camera_setup":',source)
        self.assertIn('device.get("user_id")',source)
        self.assertIn('camera_enabled": True',source)
        self.assertNotIn('"transfer_device": True', source)

    def test_runtime_worker_host_uses_existing_tafa_connection(self):
        source=(CUSTOM / "relay/relay_vision.py").read_text()
        self.assertIn('entry.options.get("gpu_base")',source)
        self.assertIn('entry.data.get("gpu_base"',source)

if __name__ == "__main__":
    unittest.main()
