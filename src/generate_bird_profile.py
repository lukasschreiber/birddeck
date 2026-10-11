import os
import shutil
import yaml
import uuid
import json
from pathlib import Path
from gen_uuid import profile_folder_id
from gen_image import generate_image
from zip import zip_profile
from gen_action import (
    generate_open_parent_folder_action,
    generate_folder_action,
    FolderType,
    generate_bird_action,
)
from PIL import Image

from pagination import paginate_elements, sort_elements
from paths import CONFIG_DIR, IMAGE_DIR, OUTPUT_DIR

BASE_DIR = Path(__file__).resolve().parent
TEMP_FOLDER = OUTPUT_DIR / "temp"
CONFIG_PATH = CONFIG_DIR / "config.yaml"


# clear it if it exists
if TEMP_FOLDER.exists():
    shutil.rmtree(TEMP_FOLDER)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)


with CONFIG_PATH.open("r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

    profile_name = config["profile"]["name"]
    main_uuid = str(uuid.uuid4()).upper()
    sd_profile_name = f"{main_uuid}.sdProfile"

    max_elements_per_page = (
        config["profile"]["size"]["columns"] * config["profile"]["size"]["rows"]
    )

    main_folder = os.path.join(
        TEMP_FOLDER, profile_name.replace(" ", ""), sd_profile_name
    )

    profiles_folder = os.path.join(main_folder, "Profiles")
    os.makedirs(profiles_folder, exist_ok=True)

    def process_page(
        entries,
        page_uuid,
        parent_name,
        has_back_to_parent=True,
        has_previous_page=False,
        next_page_uuid=None,
    ):
        print(f"Processing page {page_uuid} with {len(entries)} entries")
        # process page
        elements = {}
        page_folder_id = profile_folder_id(page_uuid)
        page_folder = os.path.join(profiles_folder, page_folder_id)
        os.makedirs(page_folder, exist_ok=True)
        os.makedirs(os.path.join(page_folder, "Images"), exist_ok=True)

        if has_back_to_parent == True:
            print(f"Adding back to parent button for page {page_uuid}")
            elements["0,0"] = generate_open_parent_folder_action()

        if has_previous_page == True:
            print(f"Adding back to previous page button for page {page_uuid}")
            previous_image = Image.open(IMAGE_DIR / "prev.png").convert("RGBA")

            previous_image_uuid = profile_folder_id(str(uuid.uuid4()))
            previous_image_path = os.path.join(
                page_folder, "Images", f"{previous_image_uuid}.png"
            )

            previous_image.save(previous_image_path)

            elements[f"0,0"] = generate_open_parent_folder_action(
                image_uuid=previous_image_uuid,
                title="",
            )

        if next_page_uuid:
            next_image = Image.open(IMAGE_DIR / "next.png").convert("RGBA")

            next_image_uuid = profile_folder_id(str(uuid.uuid4()))
            next_image_path = os.path.join(
                page_folder, "Images", f"{next_image_uuid}.png"
            )
            next_image.save(next_image_path)

            elements[
                f"{config['profile']['size']['columns'] - 1},{config['profile']['size']['rows'] - 1}"
            ] = generate_folder_action(
                folder_uuid=next_page_uuid,
                type=FolderType.MAIN,
                image_uuid=next_image_uuid,
                title="",
            )

        entries = sort_elements(entries)

        # add blank entries to make space for navigation buttons
        if has_back_to_parent == True:
            # leave first slot empty for back button
            entries = [{}] + entries
        if has_previous_page == True:
            # leave the bottom left slot empty for previous page button
            # the slot is at (0, 0) for now
            entries = [{}] + entries
        if next_page_uuid:
            # leave the bottom right slot empty for next page button
            # the slot is at (columns-1, rows-1)
            entries.insert(
                (
                    config["profile"]["size"]["rows"]
                    * config["profile"]["size"]["columns"]
                )
                - 1,
                {},
            )

        # start here to recursively create the folders and files
        for idx, entry in enumerate(entries):
            if not entry:
                continue  # skip empty entries
            row = idx // config["profile"]["size"]["columns"]
            col = idx % config["profile"]["size"]["columns"]

            # print(f"Processing entry {entry['title']} at position {col},{row}")

            if entry["type"] == "group":
                paginated_elements = paginate_elements(
                    entry["items"], max_elements_per_page
                )

                pages = []
                for page_idx, subpage in reversed(list(enumerate(paginated_elements))):
                    subpage_uuid = str(uuid.uuid4())
                    next_page_uuid = pages[0]["uuid"] if pages else None
                    page_elements = process_page(
                        subpage,
                        subpage_uuid,
                        parent_name=entry["title"],
                        has_back_to_parent=(page_idx == 0),
                        has_previous_page=(page_idx > 0),
                        next_page_uuid=next_page_uuid,
                    )
                    pages.insert(0, {"uuid": subpage_uuid, "elements": page_elements})

                # Use current page folder for the folder image, not subpage folder
                folder_image = generate_image(
                    ebird_id=entry.get("icon", ""),
                    exotic=entry.get("exotic", False),
                    favorite=entry.get("favorite", False),
                    background=entry.get("bg", entry.get("color", "#ffffff")),
                    size=(288, 288),
                )

                folder_image_uuid = profile_folder_id(str(uuid.uuid4()))
                folder_image_path = os.path.join(
                    page_folder, "Images", f"{folder_image_uuid}.png"
                )
                folder_image.save(folder_image_path)

                # Link to the first subpage of the group
                elements[f"{col},{row}"] = generate_folder_action(
                    folder_uuid=pages[0]["uuid"],
                    type=FolderType.TAXA if "icon" in entry else FolderType.MAIN,
                    image_uuid=folder_image_uuid,
                    title=entry["title"],
                )

            elif entry["type"] == "bird":
                bird_image = generate_image(
                    ebird_id=entry.get("icon", ""),
                    exotic=entry.get("exotic", False),
                    favorite=entry.get("favorite", False),
                    background=entry.get("color", "#ffffff"),
                    size=(288, 288),
                )

                bird_image_uuid = profile_folder_id(str(uuid.uuid4()))
                bird_image_path = os.path.join(
                    page_folder, "Images", f"{bird_image_uuid}.png"
                )
                bird_image.save(bird_image_path)

                elements[f"{col},{row}"] = generate_bird_action(
                    bird_name=entry["title"],
                    image_uuid=bird_image_uuid,
                    lightoom=config["profile"]["lightroom"],
                )

            elif entry["type"] == "uncertain":
                bird_image = generate_image(
                    ebird_id="",
                    background=str(IMAGE_DIR / "unknown-bird.png"),
                    size=(288, 288),
                )

                bird_image_uuid = profile_folder_id(str(uuid.uuid4()))
                bird_image_path = os.path.join(
                    page_folder, "Images", f"{bird_image_uuid}.png"
                )
                bird_image.save(bird_image_path)

                elements[f"{col},{row}"] = generate_bird_action(
                    bird_name=parent_name + " (?)",
                    image_uuid=bird_image_uuid,
                    lightoom=config["profile"]["lightroom"],
                    uncertain=True,
                )

        # print(f"Generated {len(elements)} element(s) for page {page_uuid} at {page_folder}")
        with open(
            os.path.join(page_folder, "manifest.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(
                {"Controllers": [{"Actions": elements, "Type": "Keypad"}]},
                f,
                indent=4,
            )
        return elements

    first_page_uuid = str(uuid.uuid4())
    first_page_elements = process_page(
        config["profile"]["items"], first_page_uuid, "Vogel", False
    )

    # create the main manifest.json
    manifest = {
        "AppIdentifier": config["profile"]["lightroom"],
        "Device": {"Model": config["profile"]["model"], "UUID": ""},
        "Name": profile_name,
        "Pages": {
            "Current": first_page_uuid,
            "Pages": [first_page_uuid],
            "Default": first_page_uuid,
        },
        "Version": "2.0",
    }

    with open(os.path.join(main_folder, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

zip_profile(
    os.path.join(TEMP_FOLDER, profile_name.replace(" ", "")),
    str(OUTPUT_DIR),
)
