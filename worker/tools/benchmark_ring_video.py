"""Compare 4 independent frames against 4/8/12 joint frames from ONE local MP4.

Python 3.10+ standard library only; requires locally installed ffmpeg/ffprobe.
The video is never uploaded, logged, or saved by the vision worker.
Only selected reduced JPEG frames go to the private, authenticated worker.
"""
import argparse
import base64
import ipaddress
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def _private_base(raw):
    parts = urlsplit(raw)
    if parts.scheme != "http" or not parts.hostname or parts.username or parts.password:
        raise ValueError("A private HTTP vision-worker URL is required")
    name = parts.hostname.lower()
    if name == "localhost" or name.endswith(".local"):
        return raw.rstrip("/")
    try:
        address = ipaddress.ip_address(name)
    except ValueError:
        # Hostname containing no dots = a local DNS name.
        if "." in name:
            raise ValueError("Public hostnames are not allowed for private Ring frames")
        return raw.rstrip("/")
    if not (address.is_private or address.is_loopback):
        raise ValueError("Public worker addresses are not permitted")
    return raw.rstrip("/")


def _token(env_file):
    value = os.getenv("JARVIS_TTS_TOKEN", "").strip()
    if not value and env_file:
        text = env_file.read_text(encoding="utf-8-sig")
        for row in text.splitlines():
            line = row.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, content = line.split("=", 1)
            if name.strip() == "JARVIS_TTS_TOKEN":
                value = content.strip().strip("'\"")
                break
    if len(value) < 32:
        raise ValueError("Set JARVIS_TTS_TOKEN or provide --env-file with the existing worker token")
    return value


def _run(command, *, timeout):
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Local video tool timed out") from None
    if result.returncode or not result.stdout:
        raise RuntimeError("Video could not be read with local FFmpeg tools")
    return result.stdout


def _duration(video):
    raw = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video),
    ], timeout=30)
    try:
        seconds = float(raw.decode("utf-8").strip())
    except ValueError:
        raise RuntimeError("Video has no readable duration") from None
    if not 0.5 <= seconds <= 7200:
        raise RuntimeError("Video duration is outside accepted bounds")
    return seconds


def _sample(video, second):
    image = _run([
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-ss", f"{second:.3f}", "-i", str(video), "-frames:v", "1",
        "-vf", "scale=768:768:force_original_aspect_ratio=decrease",
        "-q:v", "6", "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1",
    ], timeout=35)
    if len(image) > 2 * 1024 * 1024:
        raise RuntimeError("Sampled image exceeds the local per-frame safety limit")
    return base64.b64encode(image).decode("ascii")


def _send(base, token, *, images, mode, ctx, model):
    content = json.dumps({
        "frames": images, "mode": mode, "model": model,
        "keep_alive": 300, "num_ctx": ctx,
        "priority": "background", "wait_ms": 0,
    }, ensure_ascii=False).encode("utf-8")
    req = Request(
        base + "/benchmark/sequence", data=content, method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": token},
    )
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=450 if mode == "independent" else 150) as res:
            payload = res.read(1024 * 1024)
            answer = json.loads(payload)
            return {
                "ok": True,
                "client_ms": round((time.perf_counter() - started) * 1000, 1),
                "worker": answer,
            }
    except HTTPError as exc:
        data = exc.read(4096)
        try:
            message = json.loads(data).get("error", "HTTP error")
        except (ValueError, AttributeError):
            message = "HTTP error"
        return {
            "ok": False,
            "client_ms": round((time.perf_counter() - started) * 1000, 1),
            "error": f"HTTP {exc.code}: {message}",
        }
    except (URLError, TimeoutError, OSError):
        return {
            "ok": False,
            "client_ms": round((time.perf_counter() - started) * 1000, 1),
            "error": "Local vision worker unreachable or inference timed out",
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Private Ring multi-frame A/B benchmark")
    parser.add_argument("video", type=Path, help="An explicitly exported, authorized local MP4 clip")
    parser.add_argument("--base-url", default="http://127.0.0.1:10503",
                        help="Private vision worker URL, never a public address")
    parser.add_argument("--env-file", type=Path,
                        help="Existing worker .env file containing JARVIS_TTS_TOKEN")
    parser.add_argument("--model", default="qwen3-vl:4b-instruct",
                        choices=("qwen3-vl:2b-instruct", "qwen3-vl:4b-instruct",
                                 "qwen3-vl:8b-instruct"))
    parser.add_argument("--num-ctx", type=int, choices=(2048, 4096, 8192), default=4096)
    parser.add_argument("--output", type=Path,
                        help="Optional local results JSON (descriptions, no images or API keys)")
    opts = parser.parse_args(argv)
    if not opts.video.is_file() or opts.video.suffix.lower() != ".mp4":
        parser.error("Please choose an existing local MP4 recording")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        parser.error("ffmpeg and ffprobe must be installed and available in PATH")
    try:
        base, token = _private_base(opts.base_url), _token(opts.env_file)
        length = min(_duration(opts.video), 120)
        # All four benchmarks use exactly the same underlying 12 sampled
        # frames; 4-frame independent and joint compare identical frames.
        full = [
            {"second": round(length * (i + 0.5) / 12, 3),
             "image": _sample(opts.video, length * (i + 0.5) / 12)}
            for i in range(12)
        ]
    except (ValueError, RuntimeError, OSError) as exc:
        parser.error(str(exc))

    groups = [
        ("4 Bilder einzeln", "independent", [1, 4, 7, 10]),
        ("4 Bilder gemeinsam", "joint", [1, 4, 7, 10]),
        ("8 Bilder gemeinsam", "joint", [0, 1, 3, 4, 6, 7, 9, 10]),
        ("12 Bilder gemeinsam", "joint", list(range(12))),
    ]
    results = []
    for title, mode, indices in groups:
        print(f"\n{title} ({len(indices)} Frames):", flush=True)
        result = _send(
            base, token, images=[full[i] for i in indices],
            mode=mode, ctx=opts.num_ctx, model=opts.model,
        )
        report = {
            "test": title, "mode": mode, "frame_count": len(indices),
            "times": [full[i]["second"] for i in indices],
            **result,
        }
        results.append(report)
        print(f"  {result['client_ms'] / 1000:.2f} s",
              "OK" if result["ok"] else f"FEHLER: {result['error']}", flush=True)
        if result["ok"]:
            print("  Worker-Inferenz:",
                  f"{result['worker']['metrics']['inference_ms'] / 1000:.2f} s")
            for answer in result["worker"].get("descriptions", []):
                print("  ", answer[:500])
    baseline = results[0]["client_ms"] if results[0]["ok"] else None
    if baseline:
        print("\nVergleich zur bisherigen Einzelanalyse:")
        for row in results[1:]:
            if row["ok"]:
                ratio = row["client_ms"] / baseline
                print(f"  {row['test']}: {ratio:.2f}x der Referenzzeit")
            else:
                print(f"  {row['test']}: nicht erfolgreich")
    if opts.output:
        # No JPEGs, video bytes or authentication tokens are persisted.
        report = {
            "model": opts.model, "num_ctx": opts.num_ctx,
            "duration_sampled_seconds": round(length, 2),
            "source": opts.video.name, "results": results,
        }
        opts.output.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"\nNur der Ergebnisbericht wurde gespeichert: {opts.output}")
    return 0 if all(row["ok"] for row in results) else 2


if __name__ == "__main__":
    sys.exit(main())
