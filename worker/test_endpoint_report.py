"""Guard the deliberately compact Windows connection report."""
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parent / "Worker-Windows.ps1").read_text(encoding="utf-8")
START = SCRIPT.index("  $lines=@(", SCRIPT.index("function Write-Report {"))
END = SCRIPT.index("  [IO.File]::WriteAllLines($Report", START)
REPORT = SCRIPT[START:END]


class EndpointReportTests(unittest.TestCase):
    def test_short_endpoint_to_destination_mapping(self):
        for marker in ("10300", "10502", "11434", "gpu_stt_host",
                       "gpu_stt", "gpu_base", "llm_agent",
                       "Wyoming Protocol", "Ollama",
                       "ENGLISH - WHERE TO ENTER", "DEUTSCH - WO EINTRAGEN"):
            with self.subTest(marker=marker):
                self.assertIn(marker, REPORT)
        self.assertLess(len(REPORT.splitlines()), 46)
        for removed in ("SCHRITT FUER SCHRITT", "FIRST RUN CHECKLIST",
                        "10501", "10503", "10504", "docker compose",
                        "ANSCHLIESSEND", "qwen3:4b-instruct"):
            self.assertNotIn(removed, REPORT)
        self.assertIn("'LAN_IP'", SCRIPT)
        self.assertIn("GPU-Worker-Verbindungsdaten.txt", SCRIPT)

    def test_no_proxmox_ip_assumptions_or_secrets(self):
        self.assertNotIn("192.168.178.115", REPORT)
        self.assertNotIn("api_key", REPORT.lower())
        self.assertIn("Proxmox-Piper/MP3-Adressen sind nicht in dieser Datei bekannt", REPORT)


if __name__ == "__main__":
    unittest.main()
