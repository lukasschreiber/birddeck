import json
import math
from paths import DATA_DIR
from country_flags import validate_country
from nabu_portraits import validate_nabu_url


def load_icons():
    return json.loads((DATA_DIR / "icons.json").read_text(encoding="utf-8-sig"))


def validate_rotation(rotation):
    if type(rotation) not in (int, float) or not math.isfinite(rotation) or not -180 <= rotation <= 180:
        raise ValueError('Image rotation must be a number between -180 and 180 degrees')
    return rotation


def validate_icons(config, icons=None):
    icons = load_icons() if icons is None else icons

    def walk(items, parent):
        for item in items:
            label = f"{parent} / {item.get('title', item.get('type', 'entry'))}"
            icon = item.get("icon", "")
            validate_rotation(item.get("rotation", 0))
            validate_country(item.get("country", ""))
            validate_nabu_url(item.get("nabu", ""))
            if icon and icon not in icons:
                raise ValueError(f"{label}: unknown icon ID '{icon}' (see data/icons.json)")
            if item.get("type") == "group":
                walk(item["items"], label)

    walk(config["profile"]["items"], config["profile"]["name"])
