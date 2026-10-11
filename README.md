# BirdDeck

Build a native Stream Deck bird-tagging profile and Lightroom keyword list.
Run commands from the repository root using uv. Python 3.12 is pinned in
`.python-version`; dependencies are locked in `uv.lock`.

## Setup and usage

```powershell
uv sync --locked
uv run python scripts/download-icons.py
uv run python cli.py create
```

Import `output/BirdDeck.streamDeckProfile` into Stream Deck. Lightroom keywords
are regenerated in `output/LightroomKeywords.txt` whenever a profile is created.
Custom `--config` and `--output-dir` options apply to both generated files.

## Updating a Lightroom hierarchy with Any Tag

Export the catalog with **File > Plug-in Extras > Any Tag > Export Keywords**.
Before renaming or moving entries, bind the current YAML entries to catalog IDs:

```powershell
uv run python cli.py anytag --catalog-keywords examples/anytag.csv --bind
```

This creates `output/AnyTagKeywords.csv` and stores `anytag_id` values and
`profile.anytag_catalog` in YAML. The browser editor preserves these fields when
renaming or moving entries. IDs belong to that specific Lightroom catalog.
Exact hierarchy paths are matched first, then unique names, then unique names
with display hyphens removed. Ambiguous names stop the command; set the correct
`anytag_id` from the export on that YAML entry to resolve them.

### Routine updates

1. Open the intended catalog in Lightroom and use **File > Plug-in Extras >
   Any Tag > Export Keywords** to replace `examples/anytag.csv` with a fresh
   export. Do this for every update; earlier exports may omit newly assigned IDs.
2. Edit `config/config.yaml` or use the browser editor. Keep existing
   `anytag_id` fields when renaming or moving entries. New entries should have
   no ID. If a group and a descendant share a keyword name, give the upper
   group a distinct `tag`, such as `Star (Gruppe)`.
3. Generate the update:

```powershell
uv run python cli.py anytag --catalog-keywords examples/anytag.csv --bind
```

4. Import `output/AnyTagKeywords.csv` with **File > Plug-in Extras > Any Tag >
   Import Keywords**. Enable **Delete keywords that are not referenced in the
   imported file** to move obsolete entries out of the active hierarchy.
5. Check the result in Lightroom. Inspect `_Any Tag To Delete` before deleting
   its contents, particularly entries with photo assignments. After adding new
   keywords, export again and rerun the command with `--bind` to record their
   assigned IDs; this binding run does not require another import.

Existing keyword IDs, attributes, photo counts, synonyms,
and the catalog path are retained. New entries have blank IDs; after importing,
export again and use `--bind` to record their assigned IDs. Use `--config` and
`--output` for custom paths. Without `--bind`, YAML is left unchanged.

The YAML hierarchy is authoritative under `Vogel`. Keywords outside `Vogel`
are preserved. When the selected bird keyword has no photos and exactly one
older keyword of the same name under `Vogel` has photos, the older ID is moved
to the configured position and bound in YAML. Multiple populated alternatives
stop generation because CSV cannot merge their photo assignments. A former flat
bird that now has a same-name group retains its ID on the bird child; the group
is created separately.

Obsolete entries and empty duplicates under `Vogel` are omitted. When importing,
enable **Delete keywords that are not referenced in the imported file**.
Any Tag moves those omitted entries under `_Any Tag To Delete`, preserving
their photo assignments until you explicitly delete them in Lightroom.
The plain-text
`LightroomKeywords.txt` remains available for initial imports; use the CSV
workflow for catalog renames and moves. A keyword renamed before its first
binding needs its old catalog ID set explicitly in YAML to retain assignments.

### Catalog paths and interrupted imports

The CSV's second row and `profile.anytag_catalog` identify the catalog. The
current configuration uses `E:\Lightroom\Lightroom\Lightroom Catalog-v13-4.lrcat`.
Use a fresh export from that catalog; older exports in this repository may
reference drive `F:`. If the same catalog is moved to another drive, update
`profile.anytag_catalog` to its new path and export again. For a different
catalog, establish new bindings rather than reusing the old catalog's IDs.
Stop if Any Tag reports a different catalog; verify which catalog is open.

The generator rejects duplicate keyword paths and a keyword sharing an
ancestor's name. However, renaming a keyword to a name currently held by another
entry can still fail during import, even if the final CSV has unique paths.
This case requires two separate imports and is not automatically repaired by
the update command:

1. Prepare a CSV from the latest catalog state that retains every ID and parent
   and renames only the blocking obsolete entries to unique names, such as
   `Bachstelze (Alt 3380947)`. Import it with deletion disabled.
2. After that succeeds, import a separate CSV restoring the retained keywords'
   intended names, also with deletion disabled.
3. Export the repaired catalog again, generate a fresh hierarchy update, and
   import it with deletion of unreferenced keywords enabled.

Any Tag temporarily gives keywords UUID names during an import. If an import
fails, those names may remain; export the current state before preparing a
repair. Preserve IDs to retain photo assignments. The files
`output/AnyTagRepair01FreeNames.csv` and `output/AnyTagNameRepair.csv` were
prepared for a specific interrupted import and are not reusable repair
templates for future catalog states.

See [Any Tag's batch editing documentation](https://johnrellis.com/lightroom/anytag.htm#batch).

## Single-file installation on another laptop

Install Elgato's packaging CLI once on the build laptop (requires Node.js/npm):

```powershell
npm install -g @elgato/cli
uv run python cli.py package
```

Copy `output/de.birdtagging.names.streamDeckPlugin` to the other Windows laptop
and double-click it with Stream Deck 6.6 or newer installed. Accept Stream Deck's
bundled-profile installation prompt. The installer includes the scrolling-name
plugin, generated BirdDeck profile, key images, and action settings. Python,
Node.js, and the repository are only needed on the build laptop.

The package command rebuilds from YAML each time and overwrites the previous
installer. It supports the same `--config` and `--output-dir` options as `create`.
It stages the plugin in a temporary directory, leaving the source plugin untouched,
and uses Elgato's CLI to validate and pack it.

The default `--device-type 0` targets the configured standard 15-key Stream Deck.
For other hardware, configure the matching `profile.model` and `profile.size`
and pass the matching Elgato device type (Mini: `1`, XL: `2`, +: `7`, Neo: `9`).

Lightroom Classic must be installed separately. Set `profile.lightroom` to its
path on the receiving laptop before building. `output/LightroomKeywords.txt`
remains a separate optional Lightroom import; installing the plugin does not
import Lightroom keywords.

See Elgato's [bundled profiles](https://docs.elgato.com/streamdeck/sdk/guides/profiles/)
and [plugin packaging](https://docs.elgato.com/streamdeck/cli/commands/pack/) documentation.

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

To regroup an existing entry, choose its **Parent group** and click **Save entry**.
Choose **Profile root** to move it to the top level. Moving a group keeps all its
children; its own descendants are excluded from the destination list.

Use **Delete entry** to remove an entry after confirming. A group must have no
children before it can be deleted; delete its children first. The profile root
cannot be deleted.

Icon IDs are validated against `data/icons.json`; partial IDs show matching
suggestions. Icons are optional. Bird folders omit the eBird button when no icon is set. Unknown
icons are rejected by both the editor and profile creation.

Bird entries may set `nabu` to their HTTPS NABU portrait URL. The detail page
then includes a **NABU** website button with the NABU logo alongside **eBird**,
followed by **Paste**. Both website actions are optional and independent.
The browser editor can edit or clear the NABU link.

Each bird detail page has Back, a three-cell scrolling name, and the bird image
at the far right of the top row. The bird image uses its configured background,
including favorite and exotic colors. Tag, optional eBird/NABU links, and Paste occupy the
second row. Set the optional `scientific_name` field to show an italic scientific
name below the common name. German and English names alternate on the first line; the scientific name
scrolls separately below. All names remain editable in the web editor.
The static name image and its editor preview have been removed.

The local `plugins/de.birdtagging.names.sdPlugin` plugin renders a 272px-wide
name across three 72px cells with 20px common and 16px scientific text on pure
black. All segments share an animation clock. Both lines loop independently at 24px per second, including short names,
with a two-second pause at the start of each loop. The virtual canvas
includes two 28px gaps that are omitted from the key images.
Press any name cell to pause/resume the whole display.
The physical gaps between keys remain. Narrower decks use the available cells.

Install with `powershell -ExecutionPolicy Bypass -File plugins/install.ps1`.
The installer loads the plugin automatically when Stream Deck is running;
use `-Force` to update it. Rebuild/import with `uv run python cli.py create`.
Run plugin checks with `node --test plugins/scroll.test.cjs`.

Exotic entries are sorted by country code and then name in both the editor and
exported profile, within the existing favorite ordering. Entries without a country
come first. Exotic entries can optionally select a country by name or two-letter
code, with flags shown in the dropdown. The flag appears at the bottom-left of the preview
and exported key. Clear the country to omit the flag; disabling Exotic removes
the country when saved. Flag assets are bundled locally from [Flagpedia](https://flagpedia.net).

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

Each bird opens a folder with Back and the existing Lightroom tagging action.
Each folder also has a Paste button using the built-in Text action. It inserts
 the full display name into the active application without pressing Enter.
No extra plugin or PowerShell command is needed.
When an icon code is set, the folder also includes a website action for
`https://ebird.org/species/<icon-code>`. Uncertain entries omit this website action.
