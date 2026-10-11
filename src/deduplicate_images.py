"""Deduplicate within pages; Stream Deck requires page-local image paths."""
import hashlib
import json
import os
from pathlib import Path


def deduplicate_images(profile_dir):
    profile_dir = Path(profile_dir)
    replacements = {}
    canonical = {}
    for image in sorted((profile_dir / 'Profiles').glob('*/Images/*')):
        if not image.is_file():
            continue
        content = image.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        # Retain native-length image IDs instead of long hash filenames.
        destination = canonical.setdefault((image.parent, digest), image)
        replacements[image.resolve()] = destination

    def rewrite(value, page):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'Image' and isinstance(child, str):
                    original = (page / child).resolve()
                    if original in replacements:
                        value[key] = Path(os.path.relpath(replacements[original], page)).as_posix()
                else:
                    rewrite(child, page)
        elif isinstance(value, list):
            for child in value:
                rewrite(child, page)

    for manifest in (profile_dir / 'Profiles').glob('*/manifest.json'):
        data = json.loads(manifest.read_text(encoding='utf-8'))
        rewrite(data, manifest.parent)
        manifest.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding='utf-8')
    for image in replacements:
        if image != replacements[image].resolve():
            image.unlink()
