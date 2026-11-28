"""Tests for safe one-domain and immutable third-party integration management."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from installer import bootstrap,install,status,DOMAINS,MARKER

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.cfg=self.root/"config";self.cfg.mkdir()
  self.bundle=self.root/"bundle";self.pkg=self.bundle/"tablet_assist_for_alexa"
  self.pkg.mkdir(parents=True)
  (self.pkg/"__init__.py").write_text("def ready():\n return True\n")
  (self.pkg/"manifest.json").write_text(json.dumps({"domain":"tablet_assist_for_alexa","version":"0.4.0"}))
 def test_single_component_and_idempotence(self):
  self.assertEqual(DOMAINS,("tablet_assist_for_alexa",))
  self.assertEqual(bootstrap(self.cfg,self.bundle),["tablet_assist_for_alexa"])
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])
  target=self.cfg/"custom_components"/"tablet_assist_for_alexa"
  self.assertTrue((target/MARKER).exists())
  self.assertIn("managed by TAFA App",status(self.cfg)["tablet_assist_for_alexa"])
  self.assertFalse((self.cfg/"custom_components"/"jarvis_tablet_audio").exists())
 def test_hacs_or_manual_install_is_never_overwritten(self):
  dest=self.cfg/"custom_components"/"tablet_assist_for_alexa"
  dest.mkdir(parents=True)
  (dest/"manifest.json").write_text('{"domain":"tablet_assist_for_alexa","version":"9.9.9"}')
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])
  self.assertIn("9.9.9",status(self.cfg)["tablet_assist_for_alexa"])
 def test_upgrade_requires_unchanged_managed_files(self):
  bootstrap(self.cfg,self.bundle)
  (self.pkg/"manifest.json").write_text('{"domain":"tablet_assist_for_alexa","version":"0.4.1"}')
  self.assertEqual(len(bootstrap(self.cfg,self.bundle)),1)
  dest=self.cfg/"custom_components"/"tablet_assist_for_alexa"
  self.assertEqual(json.loads((dest/"manifest.json").read_text())["version"],"0.4.1")
  self.assertEqual(len(list((self.cfg/".tafa"/"rollback").iterdir())),1)
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])
 def test_modified_files_block_upgrade(self):
  bootstrap(self.cfg,self.bundle)
  dest=self.cfg/"custom_components"/"tablet_assist_for_alexa"
  (dest/"__init__.py").write_text("# local modification\n")
  (self.pkg/"manifest.json").write_text('{"domain":"tablet_assist_for_alexa","version":"0.5.0"}')
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])
  self.assertIn("local modification",(dest/"__init__.py").read_text())
 def test_invalid_source_is_atomic(self):
  (self.pkg/"__init__.py").write_text("def broken(")
  with self.assertRaises(SyntaxError):bootstrap(self.cfg,self.bundle)
  self.assertFalse((self.cfg/"custom_components"/"tablet_assist_for_alexa").exists())
 def test_reject_legacy_domain(self):
  with self.assertRaises(ValueError):install(self.cfg,self.bundle,domains=("jarvis_tablet_audio",))
 def test_corrupted_marker_disables_updates(self):
  bootstrap(self.cfg,self.bundle)
  dest=self.cfg/"custom_components"/"tablet_assist_for_alexa"
  (dest/MARKER).write_text("{}")
  (self.pkg/"manifest.json").write_text('{"domain":"tablet_assist_for_alexa","version":"0.5.0"}')
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])
 def test_one_time_verified_adoption_preserves_rollback(self):
  dest=self.cfg/"custom_components"/"tablet_assist_for_alexa"
  dest.mkdir(parents=True)
  old=json.dumps({"domain":"tablet_assist_for_alexa","version":"0.5.2","codeowners":["@michaelbudisch"],"documentation":"https://github.com/michaelbudisch/tablet-assist-for-alexa/blob/main/docs/marketplace.md"})
  (dest/"manifest.json").write_text(old)
  (dest/"__init__.py").write_text("# locally customized TAFA\n")
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])
  self.assertIn("locally customized",(dest/"__init__.py").read_text())
  changed=bootstrap(self.cfg,self.bundle,adopt_existing=True)
  self.assertEqual(len(changed),1)
  self.assertIn("managed by TAFA App",status(self.cfg)["tablet_assist_for_alexa"])
  backups=list((self.cfg/".tafa"/"rollback").iterdir())
  self.assertEqual(len(backups),1)
  self.assertEqual((backups[0]/"manifest.json").read_text(),old)
  self.assertIn("locally customized",(backups[0]/"__init__.py").read_text())
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])

 def test_optin_rejects_foreign_source(self):
  dest=self.cfg/"custom_components"/"tablet_assist_for_alexa"
  dest.mkdir(parents=True)
  (dest/"manifest.json").write_text(json.dumps({"domain":"tablet_assist_for_alexa","version":"0.5.2","codeowners":["@unrelated"],"documentation":"https://example.org/other"}))
  (dest/"__init__.py").write_text("# different source")
  self.assertEqual(bootstrap(self.cfg,self.bundle,adopt_existing=True),[])
  self.assertIn("different source",(dest/"__init__.py").read_text())
  self.assertFalse((self.cfg/".tafa"/"rollback").exists())

if __name__=="__main__":unittest.main()
