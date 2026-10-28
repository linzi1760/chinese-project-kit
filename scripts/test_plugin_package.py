"""Real archive checks; these do not claim LLM-trigger acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_plugin", ROOT / "tools/build_plugin.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PluginPackageTests(unittest.TestCase):
    def test_reproducible_and_safe(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second = Path(folder) / "one.zip", Path(folder) / "two.zip"
            builder.build(ROOT, first)
            builder.build(ROOT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)))
                for name in names:
                    self.assertFalse(name.startswith("/"))
                    self.assertNotIn("..", Path(name).parts)
                    self.assertNotIn("__pycache__", name)
                manifest = json.loads(archive.read("plugin.json"))
                self.assertEqual(manifest["name"], "chinese-project-kit")
                self.assertNotIn("mcpServers", manifest)
                self.assertNotIn("hooks", manifest["extensions"]["com.openai"])
                self.assertIn("skills/chinese-project-kit/SKILL.md", names)
                # Shipping source must be exact, not a second edited implementation.
                for name in builder.SKILL_FILES:
                    self.assertEqual(archive.read("skills/chinese-project-kit/" + name), (ROOT / name).read_bytes())

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "user.zip"
            output.write_bytes(b"preserve me")
            with self.assertRaises(FileExistsError):
                builder.build(ROOT, output)
            self.assertEqual(output.read_bytes(), b"preserve me")

    def test_packaged_cli_runs_after_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            archive = base / "plugin.zip"
            builder.build(ROOT, archive)
            with zipfile.ZipFile(archive) as package:
                package.extractall(base / "installed")
            scripts = base / "installed/skills/chinese-project-kit/scripts"
            project = base / "old-project"
            project.mkdir()
            original = project / "main.py"
            original.write_bytes(b"print('old project')\n")
            before = hashlib.sha256(original.read_bytes()).hexdigest()
            command = [sys.executable, str(scripts / "project_kit_agent.py"), "adopt", "--root", str(project), "--state", str(base / "outside-state")]
            first = subprocess.run(command, capture_output=True, text=True, check=True)
            second = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertIn('"created": true', first.stdout)
            self.assertIn('"created": false', second.stdout)
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main()
