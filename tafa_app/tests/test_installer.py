"""Tests for safe standalone HA App provisioning (no Home Assistant required)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from installer import bootstrap, install, status


class ProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.config = root / "ha"
        self.bundle = root / "bundle"
        self.config.mkdir()
        for domain in ("tablet_assist_for_alexa", "jarvis_tablet_audio"):
            src = self.bundle / domain
            src.mkdir(parents=True)
            (src / "manifest.json").write_text(json.dumps({"domain": domain, "version": "0.1.0"}))
            (src / "__init__.py").write_text("def ready():\n    return True\n")
        (self.bundle / "jarvis_tablet_audio" / "const.py").write_text(
            'CPU = "__JARVIS_CPU_HOST__"\nGPU = "__JARVIS_GPU_HOST__"\nSTT = "__JARVIS_CPU_STT__"\n'
        )

    def test_bootstrap_only_base(self):
        self.assertEqual(bootstrap(self.config, self.bundle), ["tablet_assist_for_alexa"])
        self.assertIn("tablet_assist_for_alexa", status(self.config))
        self.assertFalse((self.config / "custom_components" / "jarvis_tablet_audio").exists())
        self.assertEqual(bootstrap(self.config, self.bundle), [])

    def test_existing_base_not_overwritten(self):
        dest = self.config / "custom_components" / "tablet_assist_for_alexa"
        dest.mkdir(parents=True)
        (dest / "manifest.json").write_text('{"domain":"tablet_assist_for_alexa","version":"9.9.9"}')
        self.assertEqual(bootstrap(self.config, self.bundle), [])
        self.assertEqual(json.loads((dest / "manifest.json").read_text())["version"], "9.9.9")

    def test_legacy_backend_requires_valid_host_and_entities(self):
        data = dict(cpu_host="speechserver.local", gpu_host="gpu.local",
                    cpu_stt="stt.whisper", gpu_stt="stt.gpu", llm_agent="conversation.home_assistant")
        self.assertEqual(install(self.config, self.bundle, data), ["tablet_assist_for_alexa", "jarvis_tablet_audio"])
        cfg = (self.config / "custom_components" / "jarvis_tablet_audio" / "const.py").read_text()
        self.assertIn("speechserver.local", cfg)
        self.assertNotIn("__JARVIS_", cfg)

    def test_invalid_values_do_not_create_integration(self):
        with self.assertRaises(ValueError):
            install(self.config, self.bundle, dict(cpu_host="../bad", gpu_host="gpu.local", cpu_stt="stt.whisper"))
        self.assertFalse((self.config / "custom_components" / "tablet_assist_for_alexa").exists())


if __name__ == "__main__":
    unittest.main()
