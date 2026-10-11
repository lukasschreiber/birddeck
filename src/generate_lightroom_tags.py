import yaml
from pathlib import Path
from paths import CONFIG_DIR, OUTPUT_DIR


BASE_DIR = Path(__file__).resolve().parent


def flatten_items(items, depth=0, lines=None, parent_title=""):
    if lines is None:
        lines = []

    for item in items:
        item_type = item.get("type")
        title = item.get("tag", item.get("title", "Unnamed"))

        # Special case: uncertain type uses parent group title + (?)
        if item_type == "uncertain":
            title = f"{parent_title} (?)"

        lines.append("\t" * depth + title)

        # Recurse into groups
        if item_type == "group" and "items" in item:
            flatten_items(item["items"], depth + 1, lines, parent_title=title)

    return lines


def generate_keywords(config, output_dir=OUTPUT_DIR):
    items = config["profile"]["items"]

    flat_list = ["Vogel"]  # add Vogel as root title
    flatten_items(items, depth=1, lines=flat_list, parent_title="Vogel")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "LightroomKeywords.txt"
    with destination.open("w", encoding="utf-8") as out:
        out.write("\n".join(flat_list))
    return destination


def main():
    with (CONFIG_DIR / "config.yaml").open("r", encoding="utf-8-sig") as f:
        config = yaml.safe_load(f)
    print(f"Keywords ready: {generate_keywords(config)}")


if __name__ == "__main__":
    main()
