"""Persist only an original synthetic reference; never accept uploaded voice audio."""
import os
import subprocess
import sys
import wave
from pathlib import Path

REFERENCE_TEXT = (
    "Guten Tag. Alle Systeme sind bereit. Die Energieversorgung liegt im vorgesehenen Bereich. "
    "Ich habe die aktuellen Informationen geprüft und stehe für weitere Fragen zur Verfügung."
)
RATE = 24000


def valid_reference(path):
    try:
        with wave.open(str(path), "rb") as wav:
            return (wav.getframerate() == RATE and wav.getnchannels() == 1
                    and wav.getsampwidth() == 2 and RATE * 3 <= wav.getnframes() <= RATE * 60
                    and len(wav.readframes(wav.getnframes())) == wav.getnframes() * 2)
    except (OSError, ValueError, EOFError, wave.Error):
        return False


def ensure_reference(voice_id, style):
    folder = Path("/models/jarvis-voices")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (voice_id + ".wav")
    if valid_reference(path):
        print(f"Reusing fixed synthetic voice: {voice_id}", flush=True)
        return path
    print(f"Creating one-time synthetic voice: {voice_id}", flush=True)
    # A child process exits before the Base model loads, releasing its VRAM.
    # No credentials or style text are printed. The file is committed atomically.
    env = os.environ.copy()
    env["JARVIS_REFERENCE_STYLE"] = style
    subprocess.run([sys.executable, str(Path(__file__).resolve()), str(path)],
                   env=env, check=True, timeout=1800)
    if not valid_reference(path):
        raise RuntimeError("Invalid generated voice reference")
    return path


def generate(path):
    import tempfile
    import numpy as np
    import torch
    from faster_qwen3_tts import FasterQwen3TTS
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    style = os.environ["JARVIS_REFERENCE_STYLE"]
    model = FasterQwen3TTS.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign")
    chunks = []
    samples = 0
    for audio, rate, _ in model.generate_voice_design_streaming(
        text=REFERENCE_TEXT, language="German", instruct=style, chunk_size=8
    ):
        a = np.asarray(audio, dtype=np.float32).reshape(-1)
        if rate != RATE or not np.isfinite(a).all():
            raise ValueError("Invalid design audio")
        samples += a.size
        if samples > RATE * 60:
            raise ValueError("Reference too long")
        chunks.append((np.clip(a, -1, 1) * 32767).astype("<i2").tobytes())
    pcm = b"".join(chunks)
    if not pcm or not np.max(np.abs(np.frombuffer(pcm, dtype="<i2").astype(np.int32))) > 100:
        raise ValueError("No reference speech")
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".wav", delete=False) as f:
            temp = Path(f.name)
        with wave.open(str(temp), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm)
        if not valid_reference(temp):
            raise ValueError("Invalid reference WAV")
        os.replace(temp, path)
        print("Synthetic voice reference saved", flush=True)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


if __name__ == "__main__":
    generate(Path(sys.argv[1]))
