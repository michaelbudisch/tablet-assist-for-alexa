"""Guard the machine-readable import-manifest generator, not the legacy TXT."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SCRIPT=(ROOT/"Worker-Windows.ps1").read_text(encoding="utf-8")


class ManifestExportTests(unittest.TestCase):
    def test_json_contract_and_stable_id(self):
        for marker in ("tafa-worker.json", ".tafa-worker-id", "tafa-connection-v1",
                       "gpu_worker", "wyoming_stt", "qwen_tts", "ollama",
                       "enabled=$hasOllama", "enabled=$hasWhisper",
                       "ConvertTo-Json", "TryParse", "Invoke-RestMethod"):
            self.assertIn(marker,SCRIPT)
        self.assertNotIn("GPU-Worker-Verbindungsdaten.txt",SCRIPT)
        bat=(ROOT/"04-Verbindungsdaten.bat").read_text()
        self.assertIn("tafa-worker.json",bat)
        ignore=(ROOT/".gitignore").read_text()
        self.assertIn("tafa-worker.json",ignore)
        self.assertIn(".tafa-worker-id",ignore)


if __name__=="__main__":
    unittest.main()
