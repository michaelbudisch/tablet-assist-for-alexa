"""Static release validation without hardware dependencies."""
import unittest
import tempfile
import zipfile
from pathlib import Path
import check_release


class ReleaseTests(unittest.TestCase):
    def test_version_and_changelog(self):
        self.assertRegex(check_release.validate(), r"^\d+\.\d+\.\d+$")

    def test_no_secrets_or_test_audio_in_package(self):
        with tempfile.TemporaryDirectory() as directory:
            target, count = check_release.package(Path(directory) / "release.zip")
            self.assertGreater(count, 12)
            with zipfile.ZipFile(target) as archive:
                paths = archive.namelist()
                self.assertFalse(any("/.env" in n for n in paths))
                self.assertFalse(any(n.endswith((".wav", ".pcm", ".key", ".pem")) for n in paths))
                self.assertTrue(any(n.endswith("/vision/server.py") for n in paths))
                self.assertTrue(any(n.endswith("/ops/server.py") for n in paths))
                self.assertTrue(any(n.endswith("/01-Installieren.bat") for n in paths))
                self.assertTrue(any(n.endswith("/Worker-Windows.ps1") for n in paths))


if __name__ == "__main__":
    unittest.main()
