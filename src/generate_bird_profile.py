import os
from tempfile import TemporaryDirectory
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
from config_validation import validate_icons
from profile_images import image_size, save_key_image
from deduplicate_images import deduplicate_images
from bird_details import create_bird_details, bird_folder_action

def create_profile(config_path=CONFIG_DIR / "config.yaml", output_dir=OUTPUT_DIR):
    """Build a profile without modifying other outputs or temporary files."""
    config_path = Path(config_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="bird-profile-", dir=output_dir) as workspace:
        temp_folder = Path(workspace)
        with config_path.open("r", encoding="utf-8-sig") as f:
            config = yaml.safe_load(f)
            validate_icons(config)
            pixels = image_size(config['profile'])
            render_pixels = max(288, pixels)

            profile_name = config["profile"]["name"]
            if not isinstance(profile_name, str) or not profile_name.strip():
                raise ValueError("profile.name must be a non-empty string")
            if any(character in profile_name for character in '<>:"/\\|?*') or profile_name.strip() in (".", ".."):
                raise ValueError("profile.name must be a valid filename without path separators")
            main_uuid = str(uuid.uuid4()).upper()
            sd_profile_name = f"{main_uuid}.sdProfile"

            max_elements_per_page = (
                config["profile"]["size"]["columns"] * config["profile"]["size"]["rows"]
            )

            main_folder = os.path.join(
                temp_folder, profile_name.replace(" ", ""), sd_profile_name
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

                    save_key_image(previous_image, previous_image_path, pixels)

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
                    save_key_image(next_image, next_image_path, pixels)

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
                            size=(render_pixels, render_pixels),
                            corner_radius=round(render_pixels * 40 / 288),
                        )

                        folder_image_uuid = profile_folder_id(str(uuid.uuid4()))
                        folder_image_path = os.path.join(
                            page_folder, "Images", f"{folder_image_uuid}.png"
                        )
                        save_key_image(folder_image, folder_image_path, pixels)

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
                            size=(render_pixels, render_pixels),
                            corner_radius=round(render_pixels * 40 / 288),
                        )

                        bird_image_uuid = profile_folder_id(str(uuid.uuid4()))
                        bird_image_path = os.path.join(
                            page_folder, "Images", f"{bird_image_uuid}.png"
                        )
                        save_key_image(bird_image, bird_image_path, pixels)

                        detail_uuid = create_bird_details(profiles_folder, entry, bird_image, pixels, config['profile']['lightroom'], config['profile']['size']['columns'])
                        elements[f"{col},{row}"] = bird_folder_action(detail_uuid, bird_image_uuid, entry['title'])

                    elif entry["type"] == "uncertain":
                        bird_image = generate_image(
                            ebird_id="",
                            background=str(IMAGE_DIR / "unknown-bird.png"),
                            size=(render_pixels, render_pixels),
                            corner_radius=round(render_pixels * 40 / 288),
                        )

                        bird_image_uuid = profile_folder_id(str(uuid.uuid4()))
                        bird_image_path = os.path.join(
                            page_folder, "Images", f"{bird_image_uuid}.png"
                        )
                        save_key_image(bird_image, bird_image_path, pixels)

                        detail_title = parent_name + ' (?)'
                        detail_uuid = create_bird_details(profiles_folder, {'title': detail_title}, bird_image, pixels, config['profile']['lightroom'], config['profile']['size']['columns'], uncertain=True)
                        elements[f"{col},{row}"] = bird_folder_action(detail_uuid, bird_image_uuid, detail_title, uncertain=True)

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
                "AppIdentifier": "",
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

        deduplicate_images(main_folder)
        return Path(zip_profile(
            os.path.join(temp_folder, profile_name.replace(" ", "")),
            str(output_dir),
        ))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a Stream Deck bird-tagging profile.")
    parser.add_argument("--config", type=Path, default=CONFIG_DIR / "config.yaml")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    create_profile(args.config, args.output_dir)
