"""Native folder pages for bird-specific actions."""
import json
import uuid
from pathlib import Path
from gen_uuid import profile_folder_id
from gen_action import generate_bird_action, generate_folder_action, generate_open_parent_folder_action, FolderType
from profile_images import save_key_image
from paths import ROOT_DIR
from PIL import Image
from functools import lru_cache


@lru_cache(maxsize=2)
def action_image(name):
    with Image.open(ROOT_DIR / 'assets' / 'actions' / f'{name}.png') as source:
        icon = source.convert('RGBA')
    icon.thumbnail((144, 144), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (288, 288), 'black')
    canvas.paste(icon, ((288 - icon.width) // 2, 24 + (216 - icon.height) // 2), icon)
    return canvas


def create_bird_details(profiles_folder, entry, image, pixels, lightroom, columns, uncertain=False):
    page_uuid = str(uuid.uuid4())
    page = Path(profiles_folder) / profile_folder_id(page_uuid)
    (page / 'Images').mkdir(parents=True)
    image_uuid = profile_folder_id(str(uuid.uuid4()))
    save_key_image(action_image('lightroom'), page / 'Images' / f'{image_uuid}.png', pixels)
    tagging = generate_bird_action(entry['title'], image_uuid, lightroom, uncertain=uncertain)
    tagging['States'][0].update(Title='Tag', TitleAlignment='bottom')
    actions = {'0,0': generate_open_parent_folder_action()}

    def position(index):
        return f'{index % columns},{index // columns}'

    actions[position(1)] = tagging
    if entry.get('icon'):
        ebird_image_uuid = profile_folder_id(str(uuid.uuid4()))
        save_key_image(action_image('ebird'), page / 'Images' / f'{ebird_image_uuid}.png', pixels)
        actions[position(2)] = {
            'ActionID': str(uuid.uuid4()), 'LinkedTitle': True, 'Name': 'Website',
            'Plugin': {'Name': 'Website', 'UUID': 'com.elgato.streamdeck.system.website', 'Version': '1.0'},
            'UUID': 'com.elgato.streamdeck.system.website',
            'Settings': {'path': f"https://ebird.org/species/{entry['icon']}"}, 'State': 0,
            'States': [{**tagging['States'][0], 'Title': 'eBird', 'Image': f'Images/{ebird_image_uuid}.png'}],
        }
    (page / 'manifest.json').write_text(json.dumps({'Controllers': [{'Actions': actions, 'Type': 'Keypad'}]}, indent=4), encoding='utf-8')
    return page_uuid


def bird_folder_action(page_uuid, image_uuid, title, uncertain=False):
    folder = generate_folder_action(page_uuid, FolderType.MAIN, image_uuid, title)
    # Keep the original bird key label when it becomes a folder.
    folder['States'] = generate_bird_action(title, image_uuid, '', uncertain=uncertain)['States']
    return folder
