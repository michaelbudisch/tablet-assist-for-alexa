"""Stable, original synthetic TAFA voices. No uploaded or third-party audio."""
import hashlib
from pathlib import Path

from reference_voice import REFERENCE_TEXT, valid_reference

VOICE_DIR = Path("/models/jarvis-voices")  # Preserve existing persistent worker volume.
CHOICES = tuple(str(i) for i in range(1, 10))

# Variant 1 keeps the user's existing .env voice and its persisted reference.
# Other variants use deliberately different descriptions, not nine hashes of
# the identical prompt as the old worker did.
DESIGNS = {
    "1": ("Standardprofil", "Default profile", None),
    "2": ("Tief und ruhig", "Deep and calm",
          "A deep, resonant adult male voice. Low pitch, slow unhurried pace, restrained expression, precise articulate German diction."),
    "3": ("Hell und klar", "Bright and clear",
          "A bright adult female voice in a higher register. Crisp lively German articulation, light clear timbre, medium pace."),
    "4": ("Warm und weich", "Warm and gentle",
          "A warm adult female voice in a low-mid register. Smooth soft timbre, gentle and reassuring German delivery, relaxed pace."),
    "5": ("Sachlich und präzise", "Neutral and precise",
          "An androgynous adult synthetic narrator voice. Neutral mid register, dry and clear timbre, exact German articulation, even measured delivery."),
    "6": ("Markant", "Distinctive",
          "A mature adult male voice with a textured baritone timbre. Firm authoritative but natural German pronunciation, deliberate medium-slow pace."),
    "7": ("Lebendig", "Lively",
          "A youthful-sounding adult female voice with a bright energetic timbre. Expressive rhythmic German speech, brisk but understandable pace."),
    "8": ("Gelassen", "Relaxed",
          "A calm adult male voice in a soft mid register. Airy relaxed German delivery, flowing cadence, soft consonants, modest pace."),
    "9": ("Leicht und freundlich", "Light and friendly",
          "An adult female voice with a light mid-high register. Clear friendly German diction, slightly playful intonation, natural conversational pace."),
}


def variant_style(number, base_style):
    if number not in CHOICES:
        raise ValueError("Invalid variant")
    return base_style if number == "1" else DESIGNS[number][2]


def reference_id(number, base_style):
    """The original variant-1 hash is unchanged for backward compatibility."""
    style = variant_style(number, base_style)
    return hashlib.sha256(("v1\n" + style + "\n" + number + "\n" + REFERENCE_TEXT).encode("utf-8")).hexdigest()[:24]


def variant_path(number, base_style):
    return VOICE_DIR / (reference_id(number, base_style) + ".wav")


def inventory(base_style, mode):
    return [
        {"id": number, "name_de": DESIGNS[number][0], "name_en": DESIGNS[number][1],
         "ready": mode == "fixed" and valid_reference(variant_path(number, base_style))}
        for number in CHOICES
    ]
