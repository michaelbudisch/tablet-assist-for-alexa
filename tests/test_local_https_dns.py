"""Pure split-DNS tests; no root privileges or system changes."""
import importlib.util
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dns", ROOT / "proxmox/render-local-https-dns.py")
dns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dns)

class LocalHttpsDNS(unittest.TestCase):
    def test_render(self):
        conf = dns.render("HA.Example.Org", "192.168.50.20", "192.168.50.1")
        self.assertIn("listen-address=192.168.50.20", conf)
        self.assertIn("host-record=ha.example.org,192.168.50.20", conf)
        self.assertIn("local=/ha.example.org/", conf)
        self.assertIn("server=192.168.50.1", conf)
        self.assertIn("no-resolv", conf)

    def test_reject_invalid_values(self):
        for host in ("https://ha.example.org", "ha.example.org/path", "localhost",
                     "bad.example.org\nserver=8.8.8.8", "-bad.example.org"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                dns.render(host, "192.168.1.20", "192.168.1.1")
        for ip in ("8.8.8.8", "127.0.0.1", "169.254.1.1", "192.168.1.2\nserver=8.8.8.8"):
            with self.subTest(ip=ip), self.assertRaises(ValueError):
                dns.render("ha.example.org", ip, "192.168.1.1")
        with self.assertRaises(ValueError):
            dns.render("ha.example.org", "192.168.1.1", "192.168.1.1")

    def test_bash_syntax(self):
        result = subprocess.run(["bash", "-n", str(ROOT / "proxmox/install-local-https-dns.sh")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
