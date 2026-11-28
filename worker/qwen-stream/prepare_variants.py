"""Prepare original synthetic voice references from distinct fixed styles."""
import os
import sys

from reference_voice import ensure_reference
from voice_variants import CHOICES, reference_id, variant_style

DEFAULT_STYLE = (
    "A mature male voice with a warm low-mid register, calm and precise delivery, "
    "clear natural German diction, subtle British-influenced cadence, and a "
    "professional, composed tone. Moderate pace, no theatrical exaggeration."
)
style = os.environ.get("STREAM_VOICE_STYLE", DEFAULT_STYLE).strip()
if os.environ.get("STREAM_VOICE_MODE", "fast").strip().lower() != "fixed":
    raise SystemExit("Set STREAM_VOICE_MODE=fixed first")
if not 0 < len(style) <= 1000:
    raise SystemExit("Invalid style")
variants = list(dict.fromkeys(sys.argv[1:]))
if not variants or any(v not in CHOICES for v in variants):
    raise SystemExit("Usage: prepare_variants.py 2 [3 ... 9]")
for v in variants:
    ensure_reference(reference_id(v, style), variant_style(v, style))
    print(f"Variant {v} ready", flush=True)
