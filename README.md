# Bird Tagging Stream Deck

## Download bird icons

The downloaded images in `icons/` are local assets and are not tracked by Git.
The asset IDs are stored in `icons.json`.

Install the download script's dependency and run it:

```powershell
python -m pip install requests
python download-icons.py
```

The script skips existing images. It resolves its input and output paths relative
to the script, so it can also be run from another working directory.
