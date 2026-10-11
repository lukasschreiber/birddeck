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

Set `profile.image_size` in `config/config.yaml` to control the square exported
key image resolution. It defaults to `72` (72×72 pixels). For example:

```yaml
profile:
  image_size: 72
```

Images are rendered at 288 pixels or higher, then resized with Lanczos and saved
as optimized PNGs. Navigation images use the same output resolution. Supported
values are integers from 16 to 1024.

Browser previews use 288×288 images independently of the export resolution.

## Browser entry editor

```powershell
uv run python cli.py edit
uv run python cli.py edit --config config/config.yaml
uv run python cli.py edit --no-browser --port 8765
```

The CLI starts a local server and opens your browser.
The browser UI uses TypeScript, React, Material UI's default theme, and MUI X
Tree View. Node.js and npm are
needed to build it; the CLI installs the locked frontend dependencies and builds
the UI automatically on first launch. After frontend edits it rebuilds as needed.

Keep the command running while editing; press Ctrl+C in the terminal to stop it. `--no-browser` prints
the URL instead of opening it automatically.

Search and browse the hierarchy on the left and select an entry to edit its form on the
right. Select a group or the profile root and choose **Add child** to add a bird,
group, or uncertain entry. Entry types are fixed when updating existing entries
so changing a group cannot accidentally remove its children.

Icon IDs are validated against `data/icons.json`; partial IDs show matching
suggestions. Birds require an icon, while groups can leave it empty. Unknown
icons are rejected by both the editor and profile creation.

Choose **Save entry** to save the form to YAML. **Reset** discards the
current form. The browser asks before discarding unsaved changes. Comments and Unicode are
preserved, and saves are blocked if another program changes the configuration.
Rebuild with `uv run python cli.py create` to export your changes.

Frontend development checks:

```powershell
npm --prefix web run typecheck
npm --prefix web run format
npm --prefix web run build
```

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
