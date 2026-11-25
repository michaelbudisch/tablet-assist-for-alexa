"""Static and non-root regression checks for guided single-CT Proxmox setup.

No CT or VM is created by these tests, and no privileged host tools run.
"""
import importlib.util
import subprocess
import tempfile
import json
from unittest.mock import patch
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PVE = ROOT / "proxmox"
HOST = (PVE / "quick-install.sh").read_text(encoding="utf-8")
GUEST = (PVE / "install-combined-ct.sh").read_text(encoding="utf-8")
CONSOLE = (PVE / "combined-console.sh").read_text(encoding="utf-8")
DUCKDNS = (PVE / "install-duckdns-updater.sh").read_text(encoding="utf-8")
DUCKDNS_UPDATE = (PVE / "duckdns-update.py").read_text(encoding="utf-8")
AUDIO_SERVER = (ROOT / "speechserver/audio_server.py").read_text(encoding="utf-8")

spec = importlib.util.spec_from_file_location("proxy", PVE / "render-nginx-proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)
spec_dns = importlib.util.spec_from_file_location("duckdns", PVE / "duckdns-update.py")
duckdns = importlib.util.module_from_spec(spec_dns)
spec_dns.loader.exec_module(duckdns)


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

    def test_proxmox_bug_8295_unprivileged_create_umask(self):
        # PVE 9 before upstream bugfix creates the rootfs dir as 0700 when
        # pct create inherits the installer's restrictive umask 0077.
        # Require only the Proxmox create subprocess to use 0022.
        start = HOST.index('printf \\nLege neuen CT') if 'printf \\nLege neuen CT' in HOST else HOST.index("pct create")
        around = HOST[max(0, start - 450):HOST.index("CREATED=1", start)]
        self.assertIn("umask 0022", around)
        self.assertLess(around.index("umask 0022"), around.index('pct create "$CTID"'))
        self.assertIn("--unprivileged 1", around)
        self.assertIn("umask 077", HOST)

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

    def test_shared_proxy_does_not_move_public_port_forwarding(self):
        self.assertIn('ask "HTTPS-Modus (dedicated/shared/none)"', HOST)
        self.assertIn('[[ "$PROXY_CONFIRM" == JA ]]', HOST)
        self.assertIn('install-nginx-proxy.sh" prepare', HOST)
        self.assertIn('--shared', HOST)
        self.assertIn('pct exec "$PROXY_CT" -- nginx -t', HOST)
        self.assertIn('pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh', HOST)
        self.assertIn('PROXY_IP', HOST)
        self.assertIn('MODE=shared', GUEST)
        self.assertIn('JARVIS_AUDIO_ALLOW_IP', GUEST)
        self.assertIn('request.remote_addr != allowed_ip', AUDIO_SERVER)
        self.assertIn('if [[ "$MODE" == shared ]]', CONSOLE)
        self.assertNotIn('pct set "$PROXY_CT"', HOST)

    def test_duckdns_token_is_collected_inside_the_guest_not_in_host_argv(self):
        self.assertIn('install-duckdns-updater.sh', HOST)
        self.assertIn('duckdns-update.py', HOST)
        self.assertIn('read -r -s TOKEN </dev/tty', DUCKDNS)
        self.assertIn('chmod 0600 "$DEST"', DUCKDNS)
        self.assertIn('tafa-duckdns@.timer', DUCKDNS)
        self.assertIn('https://www.duckdns.org/update?', DUCKDNS_UPDATE)
        self.assertIn('www.duckdns.org', HOST)
        self.assertNotIn('pct exec "$PROXY_CT" -- bash -c "curl', HOST)

    def test_duckdns_update_is_bound_to_registered_domain_without_network(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            settings = base / "fresh-audio.json"
            token = "safe-unit-test-token-1234"
            settings.write_text(json.dumps({"domain":"fresh-audio.duckdns.org", "token":token}))
            settings.chmod(0o600)
            class FakeResponse:
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def read(self, size): return b"OK"
            calls = []
            def fake_open(request, timeout):
                calls.append((request.full_url, timeout))
                return FakeResponse()
            with patch.object(duckdns,"CONFIG_DIR",base), patch.object(duckdns,"urlopen",side_effect=fake_open):
                self.assertEqual(duckdns.update(settings), "fresh-audio.duckdns.org")
            self.assertEqual(len(calls),1)
            self.assertIn("domains=fresh-audio",calls[0][0])
            self.assertIn("token=",calls[0][0])
            self.assertTrue(calls[0][0].startswith("https://www.duckdns.org/update?"))
            settings.chmod(0o644)
            with patch.object(duckdns,"CONFIG_DIR",base), self.assertRaises(ValueError):
                duckdns.update(settings)

    def test_scripts_parse_and_status_works_without_root(self):
        for path in ("quick-install.sh", "install-combined-ct.sh", "combined-console.sh", "install-duckdns-updater.sh"):
            with self.subTest(path=path):
                subprocess.run(["bash", "-n", str(PVE / path)], check=True)
        result = subprocess.run(["bash", str(PVE / "combined-console.sh"), "--status"],
                                capture_output=True, text=True, timeout=10, check=True)
        self.assertIn("Piper TTS", result.stdout)
        self.assertIn("Wyoming STT", result.stdout)
        self.assertIn("tafa-setup", result.stdout)


if __name__ == "__main__":
    unittest.main()
