# BirdDeck

Tag selected Lightroom photos from your Stream Deck and manage the bird keyword
hierarchy from one configuration.

## First-time setup

Requires Windows, Lightroom Classic 13 or newer, Stream Deck 6.6 or newer,
[uv](https://docs.astral.sh/uv/getting-started/installation/), and Node.js/npm.
Run commands from the repository folder.

1. Install dependencies and generate the profile:

   ```powershell
   uv sync --locked
   uv run python cli.py create
   ```

2. Install the Stream Deck plugin:

   ```powershell
   powershell -ExecutionPolicy Bypass -File plugins/install.ps1 -Force
   ```

3. In Lightroom, open **File > Plug-in Manager > Add**, select
   `output/BirdDeckTagging.lrplugin`, and enable **BirdDeck Tagging**.
4. Open the intended Lightroom catalog and synchronize its keywords:

   ```powershell
   uv run python cli.py lightroom-sync
   uv run python cli.py lightroom-sync --apply
   ```

   The first command previews changes; the second applies them.
5. Import `output/BirdDeck.streamDeckProfile` into Stream Deck.

## Tag photos

Select photos in Lightroom, open a bird on the deck, and press **Tag**.
A check mark means tagging succeeded; a yellow alert means it failed.
**Paste** inserts the bird name into the active application. Press a scrolling
name button to pause or resume it.

The plugins start automatically with Lightroom and Stream Deck.

## Edit birds and groups

```powershell
uv run python cli.py edit
```

Keep the terminal running while using the browser editor. Select an entry to
edit it, or select a group and choose **Add child**. Use **Parent group** to
move an entry, then **Save entry**. A group must be empty before deleting it.
Press Ctrl+C in the terminal when finished.

You can also edit `config/config.yaml` directly. Keep existing `uuid` values
when renaming or moving entries. For new or copied entries, omit their UUIDs;
the editor or next build assigns new ones. Give groups a distinct keyword
`tag` when a child has the same name, e.g. `Star (Gruppe)` above `Star`.

## Apply your changes

With Lightroom open on the intended catalog, run:

```powershell
uv run python cli.py lightroom-sync
uv run python cli.py lightroom-sync --apply
uv run python cli.py create
```

Review the preview before applying. Import the rebuilt
`output/BirdDeck.streamDeckProfile` into Stream Deck to update the buttons.

Synchronization updates the hierarchy under `Vogel` and preserves photo
assignments. Removed entries move to `_BirdDeck Obsolete`; they are not deleted.
For a fresh catalog, open it and run the same synchronization commands.

## Files to keep

Back up `config/config.yaml` and `config/config.lightroom.json`.
The bindings file is maintained automatically; normally, edit only the YAML
or use the editor. If you move or rename an existing catalog file, update its
saved `catalog` path and the corresponding key under `catalogs` in the bindings
file before synchronizing.

## If Tag shows an alert

Check that photos are selected and BirdDeck Tagging is enabled. In Lightroom,
use **File > Plug-in Extras > Start / Restart BirdDeck Tagging**, then retry.
For new entries or another catalog, run `lightroom-sync --apply` first.
After updating the Lightroom plugin files, click **Reload Plug-in** in
Plug-in Manager and use the Start / Restart command.

Error details are in
`%USERPROFILE%\AppData\Local\BirdDeckTagging\lightroom-errors.log`.
For other command options, run `uv run python cli.py --help`.
