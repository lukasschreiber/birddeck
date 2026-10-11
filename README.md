# BirdDeck

Build a native Stream Deck bird-tagging profile and Lightroom keyword list.
Run commands from the repository root using uv. Python 3.12 is pinned in
`.python-version`; dependencies are locked in `uv.lock`.

## Setup and usage

```powershell
uv sync --locked
uv run python scripts/download-icons.py
uv run python cli.py create
uv run python src/generate_lightroom_tags.py
```

Import `output/BirdDeck.streamDeckProfile` into Stream Deck. Lightroom keywords
are written to `output/LightroomKeywords.txt`.

## Profile CLI

```powershell
uv run python cli.py --help
uv run python cli.py create --help
uv run python cli.py create --config config/config.yaml --output-dir output
```

Relative paths are resolved from the current working directory. Defaults point
to the repository's configuration and output directory. Each build uses an
isolated temporary directory that is removed automatically when the build ends.
Existing profiles with the same filename are replaced.

The downloader skips existing icons. Profile generation uses local icons when
available and downloads missing images into the image cache. Refresh the asset
ID mapping with `uv run python scripts/extract-icons.py`.

## Layout

- `src/`: profile generation, image processing, and profile utilities.
- `scripts/`: icon metadata extraction and image downloads.
- `config/`: profile configuration and its YAML schema.
- `data/`: bird metadata and icon asset IDs.
- `assets/img/`: tracked backgrounds and navigation images.
- `examples/`: the Lightroom input profile for extraction.
- `output/`: generated profiles, keyword lists, and build files (ignored).
- `.cache/`: downloaded icons and image caches (ignored).
- `.venv/`: the single uv-managed Python environment (ignored).

Extract the example with `uv run python src/unzip.py`, or pass another profile
path. Extracted files go to `output/extracted/`.
