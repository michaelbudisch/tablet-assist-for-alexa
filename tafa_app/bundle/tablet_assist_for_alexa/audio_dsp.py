"""Causal, bounded PCM processing for Jarvis; no whole-utterance buffering."""
import array
import io
import math
import sys
import wave

PROFILES = ("Natürlich", "Studio", "Klar")


def _biquad(rate, frequency, q, gain=None):
    w = 2 * math.pi * frequency / rate
    co, si = math.cos(w), math.sin(w)
    alpha = si / (2 * q)
    if gain is None:
        b0, b1, b2 = (1 + co) / 2, -(1 + co), (1 + co) / 2
        a0, a1, a2 = 1 + alpha, -2 * co, 1 - alpha
    else:
        a = 10 ** (gain / 40)
        b0, b1, b2 = 1 + alpha * a, -2 * co, 1 - alpha * a
        a0, a1, a2 = 1 + alpha / a, -2 * co, 1 - alpha / a
    return (b0/a0, b1/a0, b2/a0, a1/a0, a2/a0)


class _Stage:
    def __init__(self, coeffs):
        self.b0, self.b1, self.b2, self.a1, self.a2 = coeffs
        self.z1 = self.z2 = 0.0

    def sample(self, x):
        y = self.b0*x + self.z1
        self.z1 = self.b1*x - self.a1*y + self.z2
        self.z2 = self.b2*x - self.a2*y
        return y


class PCMFilter:
    def __init__(self, profile, rate=24000, channels=1):
        if profile not in PROFILES or not 8000 <= rate <= 48000 or channels not in (1,2):
            raise ValueError("Unsupported PCM")
        self.profile = profile
        self.channels = channels
        self.tail = b""
        self.envelope = [0.0] * channels
        self.attack = math.exp(-1/(rate*0.008))
        self.release = math.exp(-1/(rate*0.12))
        self.threshold = 0.14 if profile == "Studio" else 0.10
        self.exponent = 1/1.5-1 if profile == "Studio" else 1/2-1
        self.makeup = 1.12 if profile == "Studio" else 1.22
        coeffs = [_biquad(rate, 65 if profile == "Studio" else 85, 0.707),
                  _biquad(rate, 180 if profile == "Studio" else 230, 0.9, 1.0 if profile == "Studio" else -1.5),
                  _biquad(rate, min(2800, rate*0.36), 0.9, 1.5 if profile == "Studio" else 2.5)]
        self.stages = [[_Stage(c) for c in coeffs] for _ in range(channels)]

    def process(self, data):
        if self.profile == "Natürlich":
            return data
        data = self.tail + data
        n = len(data) - len(data) % (2*self.channels)
        self.tail = data[n:]
        if not n:
            return b""
        samples = array.array("h")
        samples.frombytes(data[:n])
        if sys.byteorder != "little":
            samples.byteswap()
        for i, v in enumerate(samples):
            ch = i % self.channels
            x = v/32768.0
            for stage in self.stages[ch]:
                x = stage.sample(x)
            level = abs(x)
            old = self.envelope[ch]
            factor = self.attack if level > old else self.release
            env = self.envelope[ch] = level + factor*(old-level)
            gain = (env/self.threshold)**self.exponent if env > self.threshold else 1.0
            x = x * gain * self.makeup
            # Instantaneous peak ceiling; no lookahead or added buffering.
            samples[i] = round(max(-0.89, min(0.89, x))*32767)
        if sys.byteorder != "little":
            samples.byteswap()
        return samples.tobytes()


def filter_wav(data, profile):
    if profile == "Natürlich":
        return data
    try:
        with wave.open(io.BytesIO(data), "rb") as src:
            if src.getsampwidth() != 2 or src.getcomptype() != "NONE":
                return data
            dsp = PCMFilter(profile, src.getframerate(), src.getnchannels())
            result = io.BytesIO()
            with wave.open(result, "wb") as dst:
                dst.setparams(src.getparams())
                while True:
                    block = src.readframes(4096)
                    if not block:
                        break
                    dst.writeframesraw(dsp.process(block))
                if dsp.tail:
                    return data
            return result.getvalue()
    except (wave.Error, EOFError, ValueError):
        return data
