"""Pure config checks; no root, no proxy deployment."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("proxy", ROOT / "proxmox/render-nginx-proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

class Proxy(unittest.TestCase):
    def test_prepare(self):
        c = proxy.render("audio.example.org", "192.0.2.10")
        self.assertIn("/.well-known/acme-challenge/", c)
        self.assertNotIn("proxy_pass ", c)
        self.assertNotIn("listen 443", c)
    def test_tls(self):
        c = proxy.render("audio.example.org", "192.0.2.10", True)
        self.assertIn(r'location ~ "^/[a-f0-9]{32}\.mp3$"', c)
        self.assertIn("proxy_pass http://192.0.2.10:8080;", c)
        self.assertIn("limit_except GET { deny all; }", c)
        self.assertIn("location / { return 404; }", c)
        self.assertNotIn(":5001", c)
        self.assertNotIn(":10300", c)
    def test_injection(self):
        for bad in ["a.example.org; include malware;", "a.example.org/path", "https://a.example.org", "a.example.org\n"]:
            with self.assertRaises(ValueError):
                proxy.render(bad, "192.0.2.10", True)
        for bad in ["127.0.0.1:5001", "foo; return 200;", 'a"b', "a/b"]:
            with self.assertRaises(ValueError):
                proxy.render("audio.example.org", bad, True)

if __name__ == "__main__":
    unittest.main()
