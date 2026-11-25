"""Inspect and remove *only* private TAFA CPU speech downloads.

The App never deletes models belonging to Wyoming, GPU, Proxmox, other HA
apps, or another integration. Deletion requires external speech mode, an
explicit Ingress confirmation, and a stopped bundled CPU worker (App restart).
"""
import shutil
from pathlib import Path

ROOT = Path("/data/tafa_speech")
VOICE = "de_DE-thorsten-medium.onnx"
VOICE_FILES = (VOICE, VOICE + ".json")


def _safe(path):
    """Never traverse symlinks even when model cache content was tampered with."""
    if ROOT.is_symlink() or path.is_symlink():
        raise ValueError("Unexpected symlink in TAFA model data")
    # Hugging Face Whisper caches legitimately use symlinks *inside*
    # snapshots/. shutil.rmtree() unlinks them without following targets.
    # Never accept a symlink as one of the top-level delete roots.


def _size(path):
    _safe(path)
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if not item.is_symlink() and item.is_file())


def inventory():
    """Current disk use in bytes. Missing files count as zero."""
    voices = ROOT / "voices"
    models = ROOT / "models"
    _safe(voices)
    return {
        "piper_bytes": sum(_size(voices / name) for name in VOICE_FILES),
        "whisper_bytes": _size(models),
    }


def remove_local_models(mode):
    """Delete known TAFA model paths only after switching to external mode."""
    if mode != "external":
        raise ValueError("Switch to external speech mode and restart before removing CPU models")
    voices = ROOT / "voices"
    models = ROOT / "models"
    _safe(ROOT)
    _safe(voices)
    _safe(models)
    for name in VOICE_FILES:
        _safe(voices / name)
    previous = inventory()
    for name in VOICE_FILES:
        file = voices / name
        if file.is_file():
            file.unlink()
    if models.is_dir():
        shutil.rmtree(models)
    return previous
