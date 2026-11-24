import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from check_audio import inspect


def sample(path, amplitude, seconds=1):
    rate = 16000
    data = [int(amplitude * math.sin(2 * math.pi * 440 * i / rate))
            for i in range(int(rate * seconds))]
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(struct.pack("<" + "h" * len(data), *data))


class AudioCheckTests(unittest.TestCase):
    def test_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "quiet.wav"
            sample(path, 20)
            report = inspect(path)
            self.assertIn("very_quiet_or_silent", report["warnings"])
            self.assertEqual(report["sample_rate"], 16000)

    def test_normal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "normal.wav"
            sample(path, 13000)
            self.assertNotIn("very_quiet_or_silent", inspect(path)["warnings"])

    def test_too_short(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.wav"
            sample(path, 1000, seconds=.1)
            self.assertIn("too_short", inspect(path)["warnings"])


if __name__ == "__main__":
    unittest.main()
