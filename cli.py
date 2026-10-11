"""Command-line interface for creating Stream Deck profiles with uv."""

import argparse
from pathlib import Path
import sys
import subprocess

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Stream Deck bird-tagging profiles.")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Create a .streamDeckProfile from YAML.")
    create.add_argument("--config", type=Path, default=ROOT_DIR / "config" / "config.yaml",
                        help="YAML configuration file (default: config/config.yaml).")
    create.add_argument("--output-dir", type=Path, default=ROOT_DIR / "output",
                        help="Destination directory (default: output/).")
    package = commands.add_parser("package", help="Build one plugin installer containing the profile.")
    package.add_argument("--config", type=Path, default=ROOT_DIR / "config" / "config.yaml")
    package.add_argument("--output-dir", type=Path, default=ROOT_DIR / "output")
    package.add_argument("--device-type", type=int, choices=range(14), default=0,
                         help="Elgato device type (default: 0, standard 15-key Stream Deck).")
    edit = commands.add_parser("edit", help="Open the browser entry editor.")
    edit.add_argument("--config", type=Path, default=ROOT_DIR / "config" / "config.yaml")
    edit.add_argument("--port", type=int, default=0, help="Local port (default: choose an available port).")
    edit.add_argument("--no-browser", action="store_true", help="Print the URL without opening a browser.")
    anytag = commands.add_parser("anytag", help="Generate a catalog-specific Any Tag hierarchy update.")
    anytag.add_argument("--config", type=Path, default=ROOT_DIR / "config" / "config.yaml")
    anytag.add_argument("--catalog-keywords", type=Path, required=True, help="Fresh Any Tag Export Keywords CSV.")
    anytag.add_argument("--output", type=Path, default=ROOT_DIR / "output" / "AnyTagKeywords.csv")
    anytag.add_argument("--bind", action="store_true", help="Store matched catalog keyword IDs in YAML for future renames/moves.")
    args = parser.parse_args(argv)

    try:
        import yaml
        if args.command == "anytag":
            from anytag_keywords import generate_anytag
            result = generate_anytag(args.config, args.catalog_keywords, args.output, args.bind)
            print(f"Any Tag update ready: {result}")
            return 0
        if args.command == "edit":
            from web_editor import run_editor
            run_editor(args.config, args.port, not args.no_browser)
            return 0
        if args.command == "package":
            from package_plugin import package_plugin
            result = package_plugin(args.config, args.output_dir, args.device_type)
        else:
            from generate_bird_profile import create_profile
            result = create_profile(args.config, args.output_dir)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Build failed: {error}\n")
    print(f"{'Installer' if args.command == 'package' else 'Profile'} ready: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
