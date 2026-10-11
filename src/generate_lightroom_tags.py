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


def main():
    with (CONFIG_DIR / "config.yaml").open("r", encoding="utf-8-sig") as f:
        config = yaml.safe_load(f)

    items = config["profile"]["items"]

    flat_list = ["Vogel"]  # add Vogel as root title
    flatten_items(items, depth=1, lines=flat_list, parent_title="Vogel")

    # print to console
    for line in flat_list:
        print(line)

    # optionally write to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / "flattened_structure.txt").open("w", encoding="utf-8") as out:
        out.write("\n".join(flat_list))


if __name__ == "__main__":
    main()
