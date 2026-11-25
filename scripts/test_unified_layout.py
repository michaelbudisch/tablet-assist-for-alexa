"""Static release guard for the single-domain TAFA App and compatibility API."""
import ast
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"custom_components"/"tablet_assist_for_alexa"
BUNDLE=ROOT/"tafa_app"/"bundle"/"tablet_assist_for_alexa"
assert not (ROOT/"tafa_app"/"bundle"/"jarvis_tablet_audio").exists()
assert set(p.relative_to(BASE) for p in BASE.rglob("*") if p.is_file() and p.suffix!=".pyc" and "__pycache__" not in p.parts) == set(
    p.relative_to(BUNDLE) for p in BUNDLE.rglob("*") if p.is_file() and p.suffix!=".pyc" and "__pycache__" not in p.parts
), "App bundle and Marketplace component must have matching files"
for p in BASE.rglob("*"):
    if not p.is_file() or p.suffix==".pyc" or "__pycache__" in p.parts:continue
    mirror=BUNDLE/p.relative_to(BASE)
    assert p.read_bytes()==mirror.read_bytes(),f"Out of date bundle: {p}"
    if p.suffix==".py":
        source=p.read_text(encoding="utf-8")
        ast.parse(source,filename=str(p))
        assert "__JARVIS_" not in source, f"Placeholder in published component: {p}"
        assert not re.search(r"192\.168\.\d+\.\d+",source),f"Private deployment host in {p}"
for path in (ROOT/"tafa_app").glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
manifest=json.loads((BASE/"manifest.json").read_text())
assert manifest["domain"]=="tablet_assist_for_alexa"
assert {"camera","binary_sensor","stt","tts","conversation"} <= set(manifest["dependencies"])
init=(BASE/"__init__.py").read_text()
assert "Platform.CAMERA" in init and "Platform.BINARY_SENSOR" in init
assert "setup_room_audio" in init and "setup_wake_devices" in init
wake=(BASE/"relay"/"relay_wake_devices.py").read_text()
assert 'url = "/api/jarvis_tablet_audio/wake_devices"' in wake
assert "jarvis_android_wakeword_routed" in wake
assert 'DOMAIN = "jarvis_tablet_audio"' in (BASE/"relay"/"const.py").read_text()
# Prevent publishing a mismatched App release or dropping the external-only mode.
config=(ROOT/"tafa_app"/"config.yaml").read_text(encoding="utf-8")
server=(ROOT/"tafa_app"/"server.py").read_text(encoding="utf-8")
docker=(ROOT/"tafa_app"/"Dockerfile").read_text(encoding="utf-8")
app_changelog=(ROOT/"tafa_app"/"CHANGELOG.md").read_text(encoding="utf-8")
version=re.search(r'^version: "([^"]+)"$',config,re.MULTILINE)
assert version, "App version missing"
assert f'APP_VERSION="{version.group(1)}"' in server, "App version mismatch"
assert "## "+version.group(1) in app_changelog, "Missing App changelog"
assert "speech_mode: list(local|external)" in config
assert "external_piper_base: str" in config
assert "speech_source.py" in docker
assert "choose_speech_source()" in server
print("TAFA unified component layout, external mode and release metadata verified")
