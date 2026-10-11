import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from package_plugin import ROOT_DIR, package_plugin


class PackagePluginTests(unittest.TestCase):
    def test_packer_receives_profile_and_manifest_without_changing_source(self):
        source = ROOT_DIR / "plugins/de.birdtagging.names.sdPlugin/manifest.json"
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            profile = output / "Custom.streamDeckProfile"
            profile.write_bytes(b"profile archive")
            staged = []

            def pack(command, check):
                self.assertTrue(check)
                plugin = Path(command[2])
                staged.append(plugin)
                manifest = json.loads((plugin / "manifest.json").read_text())
                self.assertEqual(manifest["Profiles"][0], {
                    "Name": "profiles/Custom", "DeviceType": 2,
                    "Readonly": False, "AutoInstall": True,
                    "DontAutoSwitchWhenInstalled": False,
                })
                self.assertEqual((plugin / "profiles" / profile.name).read_bytes(), profile.read_bytes())
                self.assertTrue((plugin / "plugin.js").is_file())
                self.assertEqual(manifest["Software"]["MinimumVersion"], "6.6")
                (output / "de.birdtagging.names.streamDeckPlugin").write_bytes(b"installer")

            with patch("package_plugin.shutil.which", return_value="streamdeck"), \
                    patch("package_plugin.create_profile", return_value=profile) as create, \
                    patch("package_plugin.subprocess.run", side_effect=pack):
                result = package_plugin("custom.yaml", output, 2)
            create.assert_called_once_with("custom.yaml", output)
            self.assertTrue(result.is_file())
            self.assertFalse(staged[0].exists())
        self.assertEqual(source.read_bytes(), original)

    def test_missing_cli_fails_before_generating_profile(self):
        with patch("package_plugin.shutil.which", return_value=None), \
                patch("package_plugin.create_profile") as create:
            with self.assertRaisesRegex(ValueError, "npm install"):
                package_plugin("custom.yaml", ".")
            create.assert_not_called()
