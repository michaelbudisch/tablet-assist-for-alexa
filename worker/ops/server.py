"""Private LAN, read-only Jarvis worker diagnostics (Python stdlib only).

No transcript, camera image, or request payload is stored.
Selftest is a connectivity/readiness check, NOT a GPU inference benchmark.
"""
import json
import os
import shutil
import socket
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

VERSION = "2.2.8"
SERVICES = {
    "vision": ("http://vision:10503/health", "http"),
    "tts_stream": ("http://qwen-stream:10502/health", "http"),
    "tts_legacy": ("http://qwen:10501/health", "http"),
    "ollama": ("http://ollama:11434/api/tags", "http"),
    "whisper": ("whisper", "tcp"),
}


def service_check(name, entry, timeout=1.8):
    started = time.monotonic()
    try:
        address, kind = entry
        if kind == "tcp":
            with socket.create_connection((address, 10300), timeout=timeout):
                pass
            ready, detail = True, "TCP reachable (Wyoming protocol not tested)"
        else:
            req = Request(address, headers={"Accept": "application/json"})
            with urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    raise OSError("upstream unavailable")
                result = json.loads(response.read(65536))
            ready = bool(result.get("ready", True))
            detail = "ready" if ready else "not ready"
        return {"available": ready, "detail": detail,
                "latency_ms": round((time.monotonic() - started) * 1000)}
    except (OSError, ValueError, TypeError, URLError, HTTPError, TimeoutError):
        return {"available": False, "detail": "not reachable",
                "latency_ms": round((time.monotonic() - started) * 1000)}


def gpu_check():
    """Optional NVIDIA driver metrics, never a fatal service dependency."""
    tool = shutil.which("nvidia-smi")
    if not tool:
        return {"available": False, "reason": "nvidia-smi not available"}
    try:
        run = subprocess.run(
            [tool, "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=2, check=True,
        )
        devices = []
        for line in run.stdout.splitlines()[:8]:
            values = [part.strip() for part in line.split(",")]
            if len(values) == 3 and all(value.isdecimal() for value in values):
                util, used, total = map(int, values)
                devices.append({"util_percent": util, "memory_used_mib": used,
                                "memory_total_mib": total})
        return {"available": bool(devices), "devices": devices}
    except (OSError, subprocess.SubprocessError, ValueError):
        return {"available": False, "reason": "GPU metrics unavailable"}


def status(check=service_check, gpu=gpu_check):
    checks = {name: check(name, entry) for name, entry in SERVICES.items()}
    available = sum(int(result["available"]) for result in checks.values())
    return {"worker_version": VERSION, "mode": "read-only",
            "services": checks, "gpu": gpu(),
            "overall": "ready" if available == len(checks) else
                       "degraded" if available else "unavailable",
            "note": "Unstarted Compose profiles appear unavailable; a passing status is not a model inference test"}


def make_handler(checker=status):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/health":
                return self.reply(200, {"ready": True, "worker_version": VERSION})
            if path not in ("/status", "/selftest"):
                return self.reply(404, {"error": "not found"})
            report = checker()
            if path == "/selftest":
                report = {"worker_version": VERSION,
                          "checks": report["services"],
                          "passed": sum(int(v["available"]) for v in report["services"].values()),
                          "total": len(report["services"]),
                          "limitation": "Connectivity tests only; no microphone, GPU inference, or synthesized audio test"}
            return self.reply(200, report)

        def reply(self, code, body):
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):
            # Do not log paths or data from client requests.
            pass

    return Handler


if __name__ == "__main__":
    print("Jarvis diagnostics listening on port 10504", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 10504), make_handler()).serve_forever()
