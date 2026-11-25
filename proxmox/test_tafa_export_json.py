"""Speech CT manifest exporter contract; no CT required."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE_PATH=Path(__file__).parent/"tafa-export-json.py"
spec=importlib.util.spec_from_file_location("tafa_export_json",MODULE_PATH)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExportTests(unittest.TestCase):
    def test_export_exact_sources(self):
        data=module.manifest("192.168.1.9","2823ec3a-7735-479e-958a-d3d79faab714",
                             {"piper":True,"whisper":True,"mp3":False})
        self.assertEqual(data["kind"],"speech_server")
        self.assertEqual(data["services"]["wyoming_stt"]["port"],10300)
        self.assertEqual(data["services"]["piper"]["url"],"http://192.168.1.9:5000")
        self.assertFalse(data["services"]["mp3"]["enabled"])
        self.assertEqual(data["services"]["https_audio"]["url"],"")
        with self.assertRaises(ValueError):
            module.manifest("8.8.8.8","id",{})
    def test_id_stays_across_repeated_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/"id"
            first=module.stable_identity(file)
            self.assertEqual(first,module.stable_identity(file))
            self.assertEqual(file.stat().st_mode & 0o777,0o600)


if __name__=="__main__":
    unittest.main()
