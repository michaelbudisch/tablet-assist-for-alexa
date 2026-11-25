"""Safe one-domain provisioning tests; no HA runtime required."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from installer import bootstrap,install,status,DOMAINS

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.cfg=self.root/"config";self.cfg.mkdir()
  self.bundle=self.root/"bundle";d=self.bundle/"tablet_assist_for_alexa";d.mkdir(parents=True)
  (d/"__init__.py").write_text("def ready():\n return True\n")
  (d/"manifest.json").write_text(json.dumps({"domain":"tablet_assist_for_alexa","version":"0.4.0"}))
 def test_only_one_integration(self):
  self.assertEqual(DOMAINS,("tablet_assist_for_alexa",))
  self.assertEqual(bootstrap(self.cfg,self.bundle),["tablet_assist_for_alexa"])
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])
  self.assertFalse((self.cfg/"custom_components"/"jarvis_tablet_audio").exists())
 def test_never_replace_existing(self):
  p=self.cfg/"custom_components"/"tablet_assist_for_alexa";p.mkdir(parents=True)
  (p/"manifest.json").write_text('{"version":"9.9.9"}')
  self.assertEqual(bootstrap(self.cfg,self.bundle),[])
  self.assertIn("9.9.9",status(self.cfg)["tablet_assist_for_alexa"])
 def test_reject_unknown_domain(self):
  with self.assertRaises(ValueError):
   install(self.cfg,self.bundle,{},domains=("jarvis_tablet_audio",))
 def test_invalid_bundle_without_partial_install(self):
  (self.bundle/"tablet_assist_for_alexa"/"__init__.py").write_text("def invalid(")
  with self.assertRaises(SyntaxError):
   bootstrap(self.cfg,self.bundle)
  self.assertFalse((self.cfg/"custom_components"/"tablet_assist_for_alexa").exists())
if __name__=="__main__":unittest.main()
