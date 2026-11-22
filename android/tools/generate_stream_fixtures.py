"""Development-only synthetic audio fixtures; requires lameenc, never bundled with the app."""
import math
import struct
import wave
from pathlib import Path
import lameenc

out = Path(__file__).resolve().parents[1] / 'app/src/androidTest/assets'
out.mkdir(parents=True, exist_ok=True)
for rate, channels in [(24000, 1), (44100, 2)]:
    pcm = bytearray()
    for sample in range(rate * 4):
        t = sample / rate
        value = int(9000 * math.sin(2 * math.pi * (330 * t + 60 * t * t)))
        pcm.extend(struct.pack('<h', value) * channels)
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(64 if channels == 1 else 128)
    encoder.set_in_sample_rate(rate)
    encoder.set_channels(channels)
    encoder.set_quality(2)
    mp3 = bytearray()
    for start in range(0, len(pcm), rate * channels * 2 // 10):
        mp3.extend(encoder.encode(bytes(pcm[start:start + rate * channels * 2 // 10])))
    mp3.extend(encoder.flush())
    (out / f'stream-{rate}-{channels}.mp3').write_bytes(mp3)
    if channels == 1:
        path = out / 'stream-24000-1.wav'
        with wave.open(str(path), 'wb') as audio:
            audio.setnchannels(channels)
            audio.setsampwidth(2)
            audio.setframerate(rate)
            audio.writeframes(pcm)
        data = bytearray(path.read_bytes())
        data[4:8] = bytes(4)
        data[40:44] = bytes(4)
        path.write_bytes(data)
print('Generated original 4-second synthetic MP3 and streaming-WAV fixtures.')
