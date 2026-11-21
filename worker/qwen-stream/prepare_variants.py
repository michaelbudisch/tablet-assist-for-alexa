"""Locally prepare additional original synthetic references, no voice uploads."""
import hashlib
import os
import sys
from reference_voice import REFERENCE_TEXT, ensure_reference

DEFAULT_STYLE = "A mature male voice with a warm low-mid register, calm and precise delivery, clear natural German diction, subtle British-influenced cadence, and a professional, composed tone. Moderate pace, no theatrical exaggeration."
style = os.environ.get("STREAM_VOICE_STYLE", DEFAULT_STYLE).strip()
if os.environ.get("STREAM_VOICE_MODE", "fast").strip().lower() != "fixed":
    raise SystemExit("Set STREAM_VOICE_MODE=fixed first")
if not 0 < len(style) <= 1000:
    raise SystemExit("Invalid style")
variants = list(dict.fromkeys(sys.argv[1:]))
if not variants or any(v not in tuple(str(i) for i in range(1,10)) for v in variants):
    raise SystemExit("Usage: prepare_variants.py 2 [3 ... 9]")
for v in variants:
    key = hashlib.sha256(("v1\n" + style + "\n" + v + "\n" + REFERENCE_TEXT).encode("utf-8")).hexdigest()[:24]
    ensure_reference(key, style)
    print(f"Variant {v} ready", flush=True)
