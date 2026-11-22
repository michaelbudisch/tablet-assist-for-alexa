"""Smoke-test staged Home Assistant installation without starting HA."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Install(unittest.TestCase):
    def test_render(self):
        template = ROOT / 'homeassistant' / 'config.example.json'
        with tempfile.TemporaryDirectory() as d:
            stage = Path(d) / 'stage'
            subprocess.run([sys.executable, str(ROOT / 'homeassistant' / 'install.py'),
                            '--config', str(template), '--output', str(stage)], check=True)
            pkg = stage / 'packages' / 'jarvis.yaml'
            self.assertTrue(pkg.is_file())
            self.assertIn('jarvis_initialize_defaults', pkg.read_text(encoding='utf-8'))
            self.assertTrue((stage / 'jarvis-dashboard.yaml').is_file())
            for p in stage.rglob('*'):
                if p.is_file():
                    self.assertNotIn('__JARVIS_', p.read_text(encoding='utf-8'), str(p))
                if p.suffix == '.js':
                    subprocess.run(['node', '--check', str(p)], check=True)
            panel = stage / 'www' / 'jarvis' / 'jarvis-control-panel-v1.5.js'
            self.assertIn('setConfig(config)', panel.read_text(encoding='utf-8'))
            self.assertIn('custom:echo-relay-assist-card', (stage / 'jarvis-dashboard.yaml').read_text(encoding='utf-8'))
            for name in ('echo-relay-assist-card-v1.2.0.js', 'jarvis-settings-v1.1.0.js', 'jarvis-proactive-v1.0.0.js', 'jarvis-model-settings-v1.1.0.js', 'jarvis-control-panel-v1.6.0.js'):
                self.assertTrue((stage / 'www' / 'jarvis' / name).is_file())
            for name in ('jarvis_android', 'jarvis_tablet_audio'):
                self.assertTrue((stage / 'custom_components' / name / 'manifest.json').is_file())

if __name__ == '__main__':
    unittest.main()
