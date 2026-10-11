import json
from paths import DATA_DIR


def load_icons():
    return json.loads((DATA_DIR / "icons.json").read_text(encoding="utf-8-sig"))


def validate_icons(config, icons=None):
    icons = load_icons() if icons is None else icons

    def walk(items, parent):
        for item in items:
            label = f"{parent} / {item.get('title', item.get('type', 'entry'))}"
            icon = item.get("icon", "")
            if icon and icon not in icons:
                raise ValueError(f"{label}: unknown icon ID '{icon}' (see data/icons.json)")
            if item.get("type") == "group":
                walk(item["items"], label)

    walk(config["profile"]["items"], config["profile"]["name"])
