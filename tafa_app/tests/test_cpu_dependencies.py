"""Prevent accidental upgrades to NumPy x86-64-v2 wheels in TAFA CPU images."""
import pathlib
import unittest

DOCKERFILE=pathlib.Path(__file__).resolve().parents[1]/"Dockerfile"

class CpuDependencyPolicy(unittest.TestCase):
    def test_legacy_cpu_numpy_pin_and_runtime_probe(self):
        docker=DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn('"numpy==1.26.4"',docker)
        self.assertIn("assert numpy.__version__ == '1.26.4'",docker)
        self.assertIn("from piper import PiperVoice",docker)
        self.assertIn("from faster_whisper import WhisperModel",docker)
        self.assertIn("pip check",docker)

if __name__=="__main__":
    unittest.main()
