"""Static release validation without hardware dependencies."""
import unittest
import sys
import tempfile
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_release


class ReleaseTests(unittest.TestCase):
    def test_no_required_gpu_or_mp3_api_tokens(self):
        root = Path(__file__).resolve().parents[2]
        public = (
            "worker/compose.yaml",
            "worker/qwen/server.py",
            "worker/qwen-stream/server.py",
            "worker/vision/server.py",
            "worker/ops/server.py",
            "speechserver/api.py",
            "custom_components/tablet_assist_for_alexa/config_flow.py",
        )
        for relative in public:
            with self.subTest(path=relative):
                source = (root / relative).read_text(encoding="utf-8")
                self.assertNotIn("JARVIS_TTS_TOKEN", source)
                self.assertNotIn("PIPER_API_TOKEN", source)
                self.assertNotIn("X-API-Key", source)
        for name in ("00-Konfiguration.bat", "01-Installieren.bat",
                     "02-Starten.bat", "03-Neustarten.bat",
                     "04-Verbindungsdaten.bat", "05-Vision-Einrichten.bat",
                     "scripts/windows/05-Ollama-Einrichten.bat", "scripts/windows/Worker-Windows.ps1"):
            self.assertTrue((check_release.ROOT / name).is_file(), name)

    def test_vision_has_default_install_retrofit_restart_and_readiness(self):
        ps=(check_release.ROOT/"scripts/windows/Worker-Windows.ps1").read_text(encoding="utf-8")
        self.assertIn("function Setup-Vision",ps)
        self.assertIn("'Vision' { Setup-Vision }",ps)
        self.assertIn("      Setup-Vision",ps)
        self.assertIn("ollama ollama pull $model",ps)
        self.assertIn("10503/health",ps)
        self.assertIn("$health.ready -eq $true",ps)
        self.assertIn("$known -contains 'vision'",ps)
        self.assertIn("05-Vision-Einrichten.bat",ps)
        self.assertNotIn("ollama pull qwen3:4b-instruct",ps)
        self.assertIn('profiles: ["vision"]',(check_release.ROOT/"compose.yaml").read_text())
        self.assertIn("-Action Vision",(check_release.ROOT/"05-Vision-Einrichten.bat").read_text())
        self.assertNotIn("JARVIS_TTS_TOKEN",ps)

    def test_version_and_changelog(self):
        self.assertRegex(check_release.validate(), r"^\d+\.\d+\.\d+$")

    def test_no_secrets_or_test_audio_in_package(self):
        with tempfile.TemporaryDirectory() as directory:
            target, count = check_release.package(Path(directory) / "release.zip")
            self.assertGreater(count, 12)
            with zipfile.ZipFile(target) as archive:
                paths = archive.namelist()
                self.assertFalse(any("/.env" in n for n in paths))
                self.assertFalse(any(n.endswith((".wav", ".pcm", ".key", ".pem")) for n in paths))
                self.assertTrue(any(n.endswith("/vision/server.py") for n in paths))
                self.assertTrue(any(n.endswith("/ops/server.py") for n in paths))
                self.assertTrue(any(n.endswith("/01-Installieren.bat") for n in paths))
                self.assertTrue(any(n.endswith("/docs/README.de.md") for n in paths))
                self.assertTrue(any(n.endswith("/scripts/linux/setup-linux.sh") for n in paths))
                self.assertTrue(any(n.endswith("/scripts/windows/Worker-Windows.ps1") for n in paths))


if __name__ == "__main__":
    unittest.main()
