#!/usr/bin/env python3
"""Export stable private endpoints from inside a TAFA Debian speech CT."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import uuid


def ipv4():
    raw = subprocess.check_output(["hostname", "-I"], text=True, timeout=3)
    for token in raw.split():
        try:
            ip = ipaddress.ip_address(token)
        except ValueError:
            continue
        if ip.version == 4 and ip.is_private and not ip.is_loopback:
            return str(ip)
    raise RuntimeError("No private IPv4 address on speech CT")


def running(service):
    return subprocess.run(["systemctl", "is-active", "--quiet", service],
                          check=False, timeout=3).returncode == 0


def stable_identity(path):
    if path.is_file():
        stored=path.read_text(encoding="utf-8").strip()
        try:
            return str(uuid.UUID(stored))
        except ValueError:
            pass
    identity=str(uuid.uuid4())
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(identity+"\n",encoding="utf-8")
    os.chmod(path,0o600)
    return identity


def audio_https_domain():
    hostfile=Path("/etc/tafa-combined-hostname")
    if not hostfile.is_file() or not Path("/etc/nginx/sites-enabled/tablet-assist-audio").exists():
        return ""
    host=hostfile.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9.-]{4,253}",host) or host.endswith(".local"):
        return ""
    certificate=Path("/etc/letsencrypt/live")/host/"fullchain.pem"
    return "https://"+host if certificate.is_file() and running("nginx.service") else ""


def manifest(host, device_id, enabled, public_audio=""):
    ip=ipaddress.ip_address(host)
    if ip.version != 4 or not ip.is_private or ip.is_loopback:
        raise ValueError("Expected private IPv4 host")
    return {
        "schema": "tafa-connection-v1",
        "kind": "speech_server",
        "device_id": device_id,
        "host": host,
        "services": {
            "wyoming_stt": {"host":host,"port":10300,"enabled":bool(enabled.get("whisper"))},
            "piper": {"url":f"http://{host}:5000","enabled":bool(enabled.get("piper"))},
            "mp3": {"url":f"http://{host}:5001","enabled":bool(enabled.get("mp3"))},
            "https_audio": {"url":public_audio,"enabled":bool(public_audio)},
        },
    }


def main():
    parser=argparse.ArgumentParser(description="TAFA speech CT JSON export")
    parser.add_argument("--output",default="/root/tafa-speech.json")
    args=parser.parse_args()
    identity=stable_identity(Path("/etc/tafa-manifest-id"))
    host=ipv4()
    services={name:running("jarvis-"+name+".service") for name in ("whisper","piper","mp3")}
    result=manifest(host,identity,services,audio_https_domain())
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    os.chmod(temp,0o600)
    temp.replace(target)
    print("TAFA speech-server import: "+str(target))


if __name__=="__main__":
    main()
