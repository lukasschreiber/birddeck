import os
import json
import requests

JSON_PATH = "icons.json"
OUT_DIR = "icons"

# I think the highest res is 2400 where the intrinsic size is returned
BASE_URL = "https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{asset_id}/640"

def is_valid_asset_id(v) -> bool:
    return isinstance(v, (str, int)) and str(v).strip().isdigit()

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Expected JSON to be an object/dict like {\"sthsee2\": \"153700981\", ...}")

    for species_code, asset_id in data.items():
        if not is_valid_asset_id(asset_id):
            print(f"Skipping {species_code}: invalid asset_id={asset_id!r}")
            continue

        filename = f"{species_code}.jpg"
        path = os.path.join(OUT_DIR, filename)

        if os.path.exists(path):
            print(f"Skipping {filename}, already exists")
            continue

        url = BASE_URL.format(asset_id=str(asset_id).strip())

        try:
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            with open(path, "wb") as img_file:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        img_file.write(chunk)
            print(f"Downloaded {filename} ({asset_id})")
        except requests.RequestException as e:
            print(f"Failed {species_code} ({asset_id}): {e}")

if __name__ == "__main__":
    main()
