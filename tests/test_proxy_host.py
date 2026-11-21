import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("guard", Path(__file__).resolve().parents[1] / "proxmox/check-proxy-host.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

class Guard(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(guard.conflicts("audio.example.org", 'server_name "Audio.example.org";'))
        self.assertTrue(guard.conflicts("audio.example.org", "server_name other.example.org\n audio.example.org;"))
    def test_distinct(self):
        self.assertFalse(guard.conflicts("audio.example.org", "server_name ha.example.org; # audio.example.org"))
        self.assertFalse(guard.conflicts("audio.example.org", "server_name audio.example.org.other;"))

if __name__ == "__main__":
    unittest.main()
