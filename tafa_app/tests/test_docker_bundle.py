"""Prevent packaging regressions in the TAFA Docker image."""
import ast
import re
import shlex
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]


class DockerBundleTests(unittest.TestCase):
    def test_server_local_imports_copied(self):
        docker = (APP / "Dockerfile").read_text(encoding="utf-8")
        tree = ast.parse((APP / "server.py").read_text(encoding="utf-8"))
        imports = {
            f"{node.module.split('.')[0]}.py"
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module
            and (APP / f"{node.module.split('.')[0]}.py").is_file()
        }
        copied = set()
        for args in re.findall(r"^COPY\s+(.+)$", docker, re.MULTILINE):
            words = shlex.split(args)
            if words and words[-1] == "./":
                copied.update(words[:-1])
        self.assertTrue(imports)
        self.assertEqual(imports - copied, set(), "Local imports missing from Docker COPY")
        self.assertIn("wyoming_picker.py", imports)

    def test_wyoming_import_checked_during_docker_build(self):
        docker = (APP / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("from wyoming_picker import discover_wyoming_stt, save_wyoming_selection", docker)


if __name__ == "__main__":
    unittest.main()
