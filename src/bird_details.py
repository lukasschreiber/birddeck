"""Native folder pages for bird-specific actions."""
import json
import uuid
from pathlib import Path
from gen_uuid import profile_folder_id
from gen_action import generate_bird_action, generate_folder_action, generate_open_parent_folder_action, FolderType
from profile_images import save_key_image
from paths import ROOT_DIR
from PIL import Image, ImageDraw
from functools import lru_cache
from nabu_portraits import validate_nabu_url
from name_key import render_name_key


@lru_cache(maxsize=4)
def action_image(name):
    if name == 'copy':
        canvas = Image.new('RGB', (288, 288), 'black')
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((93, 69, 187, 181), radius=8, outline='white', width=7)
        draw.rounded_rectangle((113, 87, 207, 199), radius=8, fill='black', outline='white', width=7)
        return canvas
    filename = 'nabu.webp' if name == 'nabu' else f'{name}.png'
    with Image.open(ROOT_DIR / 'assets' / 'actions' / filename) as source:
        icon = source.convert('RGBA')
    icon.thumbnail((144, 144), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (288, 288), 'black')
    canvas.paste(icon, ((288 - icon.width) // 2, 24 + (216 - icon.height) // 2), icon)
    return canvas


def paste_name_action(name, image_uuid):
    return {
        'ActionID': str(uuid.uuid4()), 'LinkedTitle': True, 'Name': 'Text',
        'UUID': 'com.elgato.streamdeck.system.text',
        'Plugin': {'Name': 'Text', 'UUID': 'com.elgato.streamdeck.system.text', 'Version': '1.0'},
        'Settings': {'pastedText': name, 'isTypingMode': False, 'isSendingEnter': False,
                     'Hotkey': {'KeyModifiers': 0, 'QTKeyCode': 33554431, 'VKeyCode': -1}},
        'State': 0,
        'States': [{'Image': f'Images/{image_uuid}.png', 'Title': 'Paste', 'TitleAlignment': 'bottom',
                    'FontSize': 9, 'TitleColor': '#ffffff', 'ShowTitle': True, 'OutlineThickness': 2}],
    }


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
    websites = []
    if entry.get('icon'):
        websites.append(('ebird', 'eBird', f"https://ebird.org/species/{entry['icon']}"))
    nabu = validate_nabu_url(entry.get('nabu', ''))
    if nabu:
        websites.append(('nabu', 'NABU', nabu))
    for index, (name, label, url) in enumerate(websites, start=2):
        website_image_uuid = profile_folder_id(str(uuid.uuid4()))
        save_key_image(action_image(name), page / 'Images' / f'{website_image_uuid}.png', pixels)
        actions[position(index)] = {
            'ActionID': str(uuid.uuid4()), 'LinkedTitle': True, 'Name': 'Website',
            'Plugin': {'Name': 'Website', 'UUID': 'com.elgato.streamdeck.system.website', 'Version': '1.0'},
            'UUID': 'com.elgato.streamdeck.system.website',
            'Settings': {'path': url}, 'State': 0,
            'States': [{**tagging['States'][0], 'Title': label, 'Image': f'Images/{website_image_uuid}.png'}],
        }
    copy_image_uuid = profile_folder_id(str(uuid.uuid4()))
    save_key_image(action_image('copy'), page / 'Images' / f'{copy_image_uuid}.png', pixels)
    actions[position(2 + len(websites))] = paste_name_action(entry['title'], copy_image_uuid)
    if not uncertain:
        name_image_uuid = profile_folder_id(str(uuid.uuid4()))
        save_key_image(render_name_key(entry['title'], entry.get('scientific_name', '')),
                       page / 'Images' / f'{name_image_uuid}.png', pixels)
        actions[position(3 + len(websites))] = {
            'ActionID': str(uuid.uuid4()), 'LinkedTitle': True, 'Name': 'Bird name',
            'Plugin': {'Name': 'Multi Action', 'UUID': 'com.elgato.streamdeck.multiactions', 'Version': '1.0'},
            'UUID': 'com.elgato.streamdeck.multiactions.routine',
            'Actions': [], 'Settings': {}, 'State': 0,
            'States': [{'Image': f'Images/{name_image_uuid}.png', 'ShowTitle': False, 'Title': ''}],
        }
    (page / 'manifest.json').write_text(json.dumps({'Controllers': [{'Actions': actions, 'Type': 'Keypad'}]}, indent=4), encoding='utf-8')
    return page_uuid


def bird_folder_action(page_uuid, image_uuid, title, uncertain=False):
    folder = generate_folder_action(page_uuid, FolderType.MAIN, image_uuid, title)
    # Keep the original bird key label when it becomes a folder.
    folder['States'] = generate_bird_action(title, image_uuid, '', uncertain=uncertain)['States']
    return folder
