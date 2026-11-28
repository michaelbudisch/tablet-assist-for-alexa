"""Tests for safe private TAFA frontend asset cleanup (stdlib only)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tafa_frontend_cleanup.py"
SPEC = importlib.util.spec_from_file_location("tafa_frontend_cleanup", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class FrontendAssetPolicyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "www" / "tafa").mkdir(parents=True)
        (self.root / ".storage").mkdir()
        (self.root / ".storage" / "lovelace_resources").write_text(json.dumps({
            "data": {"items": [{"url": "/local/tafa/hauszentrale-main.js?v=0.5.10"}]}
        }), encoding="utf-8")
        (self.root / "www" / "tafa" / "frontend-build.json").write_text(json.dumps({
            "version": "0.5.10",
            "main": "/local/tafa/hauszentrale-main.js?v=0.5.10",
        }), encoding="utf-8")
        self.add("hauszentrale-main.js", "import('/local/tafa/ambient-night-v0.4.8.js')")
        self.add("ambient-night.js", "const version = 'stable';")
        for name in ("hauszentrale-main", "ambient-night"):
            for version in ("0.4.7", "0.4.8", "0.4.9"):
                self.add(f"{name}-v{version}.js", f"previous content: {name} {version}")

    def add(self, name, contents):
        path = self.root / "www" / "tafa" / name
        path.write_text(contents, encoding="utf-8")

    def test_dry_run_preserves_live_imports_and_latest_rollback(self):
        result = MODULE.plan(self.root)
        self.assertTrue(result["resources_read"])
        self.assertTrue(result["resource_matches_manifest"])
        names = {path.name for path in result["remove"]}
        self.assertEqual(names, {
            "hauszentrale-main-v0.4.7.js",
            "hauszentrale-main-v0.4.8.js",
            "ambient-night-v0.4.7.js",
        })
        self.assertTrue((self.root / "www/tafa/hauszentrale-main-v0.4.7.js").exists())

    def test_archival_backup_is_verified_before_removal(self):
        result = MODULE.plan(self.root)
        backup = MODULE.archive_and_remove(self.root, result["remove"])
        self.assertIsNotNone(backup)
        self.assertTrue(backup.exists())
        self.assertFalse(any(f.exists() for f in result["remove"]))
        with ZipFile(backup) as zipped:
            self.assertIsNone(zipped.testzip())
            manifest = json.loads(zipped.read("tafa-archive-manifest.json"))
            self.assertEqual(len(manifest["sha256"]), 3)
            self.assertTrue(zipped.read("www/tafa/hauszentrale-main-v0.4.7.js"))
        self.assertEqual(MODULE.plan(self.root)["remove"], [])

    def test_mismatched_resource_is_detected(self):
        resource = self.root / ".storage" / "lovelace_resources"
        resource.write_text(json.dumps({"data": {"items": [{
            "url": "/local/tafa/hauszentrale-main.js?v=0.5.9",
        }]}}), encoding="utf-8")
        result = MODULE.plan(self.root)
        self.assertFalse(result["resource_matches_manifest"])

    def test_missing_registry_is_not_approved_for_apply(self):
        (self.root / ".storage" / "lovelace_resources").unlink()
        result = MODULE.plan(self.root)
        self.assertFalse(result["resources_read"])
        self.assertFalse(result["resource_matches_manifest"])

    def test_invalid_build_blocks_cleanup(self):
        path = self.root / "www/tafa/frontend-build.json"
        path.write_text(json.dumps({"version": "0.5.10", "main": "/local/tafa/hauszentrale-main.js?v=0.5.9"}))
        with self.assertRaises(ValueError):
            MODULE.plan(self.root)


if __name__ == "__main__":
    unittest.main()
