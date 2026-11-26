"""Read-only live diagnostics must not probe unsafe destinations."""
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import socket

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import connection_probes as checks


class Response:
    def __init__(self, status, body=b'{"ready":true}'):
        self.status, self.body = status, body
    def read(self, max_bytes):
        return self.body[:max_bytes]


class HTTP:
    def __init__(self, ip, port, timeout):
        self.ip, self.port, self.timeout = ip, port, timeout
    def request(self, method, path, headers):
        assert method == "GET" and path == "/health"
        assert "Authorization" not in headers
    def getresponse(self):
        return Response(200)
    def close(self):
        pass


class Context:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def settimeout(self, value):
        pass


class TLS:
    def wrap_socket(self, sock, server_hostname):
        return Context()


class LiveConnectionProbeTests(unittest.TestCase):
    def test_invalid_field_and_private_service_are_not_contacted(self):
        with patch.object(checks.socket, "getaddrinfo") as dns, \
             patch.object(checks.socket, "create_connection") as conn:
            for field, url in [
                ("arbitrary", "http://192.168.1.50:5000"),
                ("gpu_base", "http://8.8.8.8:10502"),
                ("gpu_base", "http://user:password@192.168.1.5:10502"),
                ("mp3_base", "https://192.168.1.5:5001"),
                ("gpu_base", "http://127.0.0.1:5000"),
                ("gpu_stt_host", "example.com:1234"),
                ("public_audio_base", "http://audio.example.org"),
                ("public_audio_base", "https://audio.example.org/path"),
                ("public_audio_base", "https://audio.example.org:2222"),
                ("public_audio_base", "https://192.168.1.40"),
            ]:
                with self.subTest(field=field, url=url):
                    self.assertEqual(checks.probe_connection(field, url)["status"],
                                     "invalid")
            dns.assert_not_called()
            conn.assert_not_called()

    def test_private_health_endpoint_reports_readiness(self):
        with patch.object(checks, "_resolve", return_value=["192.168.1.10"]), \
             patch.object(checks.http.client, "HTTPConnection", HTTP):
            self.assertEqual(checks.probe_connection(
                "gpu_base", "http://192.168.1.10:10502"),
                {"status": "ready", "detail": "health"})

    def test_dns_rebinding_is_rejected(self):
        # Even a .local name cannot be used to contact non-RFC1918 IPs.
        dns_reply = [(socket.AF_INET, socket.SOCK_STREAM, 0, "",
                      ("127.0.0.1", 5000))]
        with patch.object(checks.socket, "getaddrinfo", return_value=dns_reply), \
             patch.object(checks.http.client, "HTTPConnection") as conn:
            result = checks.probe_connection(
                "external_piper_base", "http://tafa-device.local:5000")
            self.assertEqual(result["status"], "invalid")
            conn.assert_not_called()

    def test_public_domain_dns_must_not_point_to_lan(self):
        dns_reply = [(socket.AF_INET, socket.SOCK_STREAM, 0, "",
                      ("192.168.1.10", 443))]
        with patch.object(checks.socket, "getaddrinfo", return_value=dns_reply), \
             patch.object(checks.socket, "create_connection") as connect:
            result = checks.probe_connection(
                "public_audio_base", "https://audio.example.org")
            self.assertEqual(result["status"], "invalid")
            connect.assert_not_called()

    def test_public_tls_only_never_fetches_audio(self):
        with patch.object(checks, "_resolve", return_value=["203.0.113.7"]), \
             patch.object(checks.socket, "create_connection", return_value=Context()) as conn, \
             patch.object(checks.ssl, "create_default_context", return_value=TLS()):
            self.assertEqual(checks.probe_connection(
                "public_audio_base", "https://audio.example.org"),
                {"status": "tls_ok", "detail": "tls_only"})
            conn.assert_called_once_with(("203.0.113.7", 443), timeout=1.5)

    def test_missing_and_oversized_inputs_have_no_network_access(self):
        with patch.object(checks.socket, "getaddrinfo") as dns:
            self.assertEqual(checks.probe_connection(
                "public_audio_base", "")["status"], "missing")
            self.assertEqual(checks.probe_connection(
                "gpu_base", "a" * 500)["status"], "invalid")
            dns.assert_not_called()


if __name__ == "__main__":
    unittest.main()
