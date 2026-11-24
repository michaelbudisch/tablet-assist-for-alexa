"""Offline WAV quality check for Whisper troubleshooting.

No upload, transcription or persistence. Standard library only.
Run: python tools/check_audio.py path/to/microphone.wav
"""
import argparse
import json
import math
from pathlib import Path
import struct
import wave

MAX_BYTES = 25 * 1024 * 1024


def inspect(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("WAV missing or too large")
    with wave.open(str(path), "rb") as sound:
        channels, width, rate, count = sound.getnchannels(), sound.getsampwidth(), sound.getframerate(), sound.getnframes()
        if channels not in (1, 2) or width != 2 or not 8000 <= rate <= 96000:
            raise ValueError("Expected 16-bit PCM WAV, mono or stereo")
        if count > rate * 60:
            raise ValueError("Recording exceeds 60 seconds")
        data = sound.readframes(count)
    if not data:
        raise ValueError("Empty WAV")
    nums = struct.unpack("<" + "h" * (len(data) // 2), data)
    # Quantities, never the raw waveform, are returned.
    peak = max(abs(x) for x in nums) / 32768
    rms = math.sqrt(sum(x * x for x in nums) / len(nums)) / 32768
    clipped = sum(abs(x) >= 32760 for x in nums) / len(nums)
    seconds = count / rate
    flags = []
    if seconds < 0.5:
        flags.append("too_short")
    if rms < 0.007:
        flags.append("very_quiet_or_silent")
    if clipped > 0.005:
        flags.append("clipping")
    if peak < 0.03:
        flags.append("low_peak")
    return {"duration_seconds": round(seconds, 2), "sample_rate": rate,
            "channels": channels, "rms_percent": round(rms * 100, 2),
            "peak_percent": round(peak * 100, 2),
            "clipped_percent": round(clipped * 100, 3),
            "warnings": flags,
            "limitation": "Audio quality hints only; not voice activity detection or transcription"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wav", help="Local PCM WAV (never uploaded)")
    args = parser.parse_args()
    print(json.dumps(inspect(args.wav), indent=2))


if __name__ == "__main__":
    main()
