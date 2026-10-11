"""Build a plugin installer containing the generated BirdDeck profile."""

import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from generate_bird_profile import create_profile

ROOT_DIR = Path(__file__).resolve().parents[1]


def package_plugin(config_path, output_dir, device_type=0):
    output_dir = Path(output_dir).resolve()
    packer = shutil.which("streamdeck") or shutil.which("streamdeck.cmd")
    if not packer:
        raise ValueError("Stream Deck CLI is required to package: npm install -g @elgato/cli")
    source = ROOT_DIR / 'plugins' / 'de.birdtagging.names.sdPlugin'
    if not (source / 'node_modules' / '@napi-rs' / 'canvas').is_dir():
        raise ValueError('Install plugin dependencies first: npm ci --omit=dev --prefix plugins/de.birdtagging.names.sdPlugin')
    profile = create_profile(config_path, output_dir)
    with TemporaryDirectory(prefix="bird-plugin-", dir=output_dir) as workspace:
        plugin = Path(workspace) / "de.birdtagging.names.sdPlugin"
        shutil.copytree(ROOT_DIR / "plugins" / plugin.name, plugin)
        profiles = plugin / "profiles"
        profiles.mkdir(exist_ok=True)
        shutil.copy2(profile, profiles / profile.name)
        manifest_path = plugin / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["Software"]["MinimumVersion"] = "6.6"
        manifest["Profiles"] = [{
            "Name": f"profiles/{profile.stem}",
            "DeviceType": device_type,
            "Readonly": False,
            "AutoInstall": True,
            "DontAutoSwitchWhenInstalled": False,
        }]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        subprocess.run([
            packer, "pack", str(plugin), "--output", str(output_dir),
            "--force", "--no-file-list",
        ], check=True)
        result = output_dir / f"{manifest['UUID']}.streamDeckPlugin"
        if not result.is_file():
            raise ValueError(f"Packer did not produce the expected installer: {result}")
        return result
