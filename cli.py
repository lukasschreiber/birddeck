"""Command-line interface for creating Stream Deck profiles with uv."""

import argparse
from pathlib import Path
import sys

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
    args = parser.parse_args(argv)

    try:
        import yaml
        from generate_bird_profile import create_profile
        result = create_profile(args.config, args.output_dir)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        parser.exit(1, f"Error creating profile: {error}\n")
    print(f"Profile ready: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
