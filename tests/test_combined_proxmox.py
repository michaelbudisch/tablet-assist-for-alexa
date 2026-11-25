"""Static and non-root regression checks for guided single-CT Proxmox setup.

No CT or VM is created by these tests, and no privileged host tools run.
"""
import importlib.util
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PVE = ROOT / "proxmox"
HOST = (PVE / "quick-install.sh").read_text(encoding="utf-8")
GUEST = (PVE / "install-combined-ct.sh").read_text(encoding="utf-8")
CONSOLE = (PVE / "combined-console.sh").read_text(encoding="utf-8")

spec = importlib.util.spec_from_file_location("proxy", PVE / "render-nginx-proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


class CombinedCTTests(unittest.TestCase):
    def test_new_unprivileged_container_only_after_confirmation(self):
        self.assertIn('pct create "$CTID"', HOST)
        self.assertIn('--unprivileged 1', HOST)
        self.assertIn('pct config "$CTID"', HOST)
        self.assertIn('qm config "$CTID"', HOST)
        self.assertIn('[[ "$CONFIRM" == "$CTID" ]]', HOST)
        self.assertLess(HOST.index('[[ "$CONFIRM" == "$CTID" ]]'),
                        HOST.index('pct create "$CTID"'))
        self.assertNotIn("pct destroy", HOST)
        self.assertNotIn("qm destroy", HOST)
        self.assertNotIn("pct set 101", HOST)
        self.assertNotIn("pct set 102", HOST)
        self.assertIn("--rootfs", HOST)
        self.assertIn("pveam download", HOST)

    def test_guest_does_not_install_on_pve_host(self):
        self.assertIn("command -v pveversion", GUEST)
        self.assertIn("Already installed", GUEST) if "Already installed" in GUEST else self.assertIn("Existing installation", GUEST)
        self.assertIn('bash "$HERE/install-speechserver.sh"', GUEST)
        self.assertIn("install-nginx-proxy.sh", GUEST)
        self.assertIn('127.0.0.1:8080', GUEST)
        self.assertIn('127.0.0.1', GUEST)
        self.assertIn('JARVIS_GPU_BASE', GUEST)
        self.assertIn('systemctl is-active --quiet jarvis-audio', GUEST)

    def test_nginx_local_upstream_never_exposes_generator(self):
        conf = proxy.render("audio.example.org", "127.0.0.1", tls=True)
        self.assertIn("proxy_pass http://127.0.0.1:8080;", conf)
        self.assertIn('location ~ "^/[a-f0-9]{32}\.mp3$"', conf)
        self.assertIn("limit_except GET { deny all; }", conf)
        self.assertIn("location / { return 404; }", conf)
        self.assertNotIn("proxy_pass http://127.0.0.1:5001", conf)

    def test_persistent_guest_console_and_manual_https(self):
        self.assertIn("/etc/issue", CONSOLE)
        self.assertIn("/etc/motd", CONSOLE)
        self.assertIn("tafa-setup", CONSOLE)
        self.assertIn('certbot certonly --webroot', CONSOLE)
        self.assertIn('bash "$INSTALLER" enable "$HOST" 127.0.0.1', CONSOLE)
        self.assertIn('[[ "$ANSWER" == "JA" ]]', CONSOLE)
        self.assertIn('tafa-console-info.timer', GUEST)
        self.assertIn("OnUnitActiveSec=5min", GUEST)
        self.assertNotIn("iptables -A", HOST + GUEST + CONSOLE)

    def test_scripts_parse_and_status_works_without_root(self):
        for path in ("quick-install.sh", "install-combined-ct.sh", "combined-console.sh"):
            with self.subTest(path=path):
                subprocess.run(["bash", "-n", str(PVE / path)], check=True)
        result = subprocess.run(["bash", str(PVE / "combined-console.sh"), "--status"],
                                capture_output=True, text=True, timeout=10, check=True)
        self.assertIn("Piper TTS", result.stdout)
        self.assertIn("Wyoming STT", result.stdout)
        self.assertIn("tafa-setup", result.stdout)


if __name__ == "__main__":
    unittest.main()
