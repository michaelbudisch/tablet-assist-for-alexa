"""Public onboarding/documentation guardrails; keep legacy docs archived separately."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = [
    "README.md", "README.de.md",
    "android/README.md", "android/README.de.md",
    "android/docs/camera-preparation.md", "android/docs/camera-preparation.de.md",
    "tafa_app/README.md", "tafa_app/DOCS.md",
    "worker/README.md", "worker/docs/README.md", "worker/docs/README.de.md",
    "worker/docs/README.en.md",
    "docs/setup-guide.md", "docs/en/setup-guide.md",
    "docs/app.md", "docs/en/app.md",
    "docs/proxmox.md", "docs/en/proxmox.md",
    "docs/worker.md", "docs/en/worker.md",
    "docs/marketplace.md", "docs/en/marketplace.md",
    "docs/native-only.md", "docs/en/native-only.md",
    "docs/ha-automations.md", "docs/en/ha-automations.md",
    "docs/home-assistant.md", "docs/en/home-assistant.md",
    "docs/echo-relay-dashboard.md", "docs/en/echo-relay-dashboard.md",
    "docs/nginx-proxy.md", "docs/en/nginx-proxy.md",
    "docs/local-https.md", "docs/en/local-https.md",
    "docs/security.md", "docs/en/security.md",
    "docs/data-sources.md", "docs/en/data-sources.md",
    "homeassistant/examples/MULTIROOM.md", "homeassistant/examples/MULTIROOM.de.md",
    "homeassistant/examples/RING.md", "homeassistant/examples/RING.de.md",
]

# Markdown link targets only. External endpoints and #anchors have their own semantics.
LINKS = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
PRIVATE_SETUP_FRAGMENTS = (
    "ShapeAnywhere-MCP", "CT 101 bleibt", "Deine lokale Kiosk-Version",
    "Deine bereits installierte Lovelace-Vorschau",
    "deinen vorhandenen Proxmox-Sprachserver exklusiv",
)

class PublicDocumentationTests(unittest.TestCase):
    def test_relative_links_exist(self):
        for name in ACTIVE:
            path = ROOT / name
            with self.subTest(file=name):
                self.assertTrue(path.is_file(), f"Missing required public guide: {name}")
            if not path.is_file():
                continue
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for match in LINKS.finditer(line):
                    target = match.group(1).split(' "', 1)[0].strip().strip("<>")
                    target = unquote(target).split("#", 1)[0].split("?", 1)[0]
                    if not target or re.match(r"^(?:https?://|mailto:|data:|/)", target):
                        continue
                    resolved = (path.parent / target).resolve()
                    with self.subTest(file=name, line=lineno, target=target):
                        self.assertTrue(resolved == ROOT or ROOT in resolved.parents,
                                        "Link leaves repository")
                        self.assertTrue(resolved.exists(), f"Broken relative link: {name}:{lineno} -> {target}")

    def test_no_household_specific_first_time_instructions(self):
        for name in ACTIVE:
            data = (ROOT / name).read_text(encoding="utf-8")
            for fragment in PRIVATE_SETUP_FRAGMENTS:
                with self.subTest(file=name, fragment=fragment):
                    self.assertNotIn(fragment, data)

    def test_config_and_worker_docs_contract(self):
        app = (ROOT / "tafa_app/config.yaml").read_text(encoding="utf-8")
        self.assertRegex(app, r"(?m)^  speech_mode: setup$")
        self.assertIn('version: "0.4.38"', app)
        self.assertEqual((ROOT / "worker/VERSION").read_text().strip(), "2.2.6")
        self.assertEqual((ROOT / "android/VERSION").read_text().strip(), "1.2.3")
        for name in ("proxmox/quick-install.sh", "proxmox/resume-install.sh"):
            with self.subTest(script=name):
                script = (ROOT / name).read_text(encoding="utf-8")
                self.assertNotIn('Nginx proxy CT ID" "101"', script)
                self.assertNotIn('PROXY_CT="${REPLY_VALUE:-101}"', script)
        powershell = (ROOT / "worker/scripts/windows/Worker-Windows.ps1").read_text(encoding="utf-8")
        self.assertIn("tafa-worker.json", powershell)
        self.assertIn("GPU-Worker-Verbindungsdaten.txt", powershell)
        self.assertNotIn("TAFA > Einstellungen: passende GPU-Wyoming-STT", powershell)
        self.assertNotIn("TAFA > Einstellungen: Ollama-Gespraechsentitaet", powershell)
        self.assertIn("CPU-LLM-Fallback", powershell)

if __name__ == "__main__":
    unittest.main(verbosity=2)
