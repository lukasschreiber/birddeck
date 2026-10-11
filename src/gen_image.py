from PIL import Image, ImageDraw, ImageColor
import os
import re
import json
import requests
import hashlib
import numpy as np
from scipy import ndimage
from io import BytesIO
from paths import ROOT_DIR, DATA_DIR, OUTPUT_DIR, CACHE_DIR as PROJECT_CACHE_DIR


# === CONFIG ===
CACHE_DIR = PROJECT_CACHE_DIR / "images"
os.makedirs(CACHE_DIR, exist_ok=True)


# === CACHE UTILITIES ===
def _cache_path(url: str) -> str:
    """Return file path for cached image."""
    filename = hashlib.md5(url.encode("utf-8")).hexdigest() + ".png"
    return os.path.join(CACHE_DIR, filename)


def get_cached_image(url: str) -> Image.Image | None:
    """Return cached image if available, else None."""
    path = _cache_path(url)
    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA")
        except Exception:
            os.remove(path)  # remove corrupted cache
    return None


def save_to_cache(url: str, image: Image.Image) -> None:
    """Save image to cache folder."""
    path = _cache_path(url)
    image.save(path, "PNG")


# === IMAGE FETCHING ===
def fetch_image(url: str) -> Image.Image | None:
    """Fetch image from cache or download it."""
    cached = get_cached_image(url)
    if cached:
        return cached

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        save_to_cache(url, img)
        return img
    except Exception as e:
        print(f"Error fetching image from {url}: {e}")
        return None


# === BACKGROUND REMOVAL ===
def remove_largest_white_background(image: Image.Image) -> Image.Image:
    """
    Remove only the largest connected region of white-ish pixels
    (R,G,B > 250), keeping white details inside the subject.
    """
    threshold = 245
    feather_radius = 1
    arr = np.array(image)
    if arr.shape[2] == 3:
        arr = np.dstack([arr, np.full(arr.shape[:2], 255, dtype=np.uint8)])

    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

    # Identify "white-ish" pixels
    white_mask = (r > threshold) & (g > threshold) & (b > threshold)

    # Label connected components in white regions
    labeled, num = ndimage.label(white_mask)  # type: ignore
    if num == 0:
        return image

    # Find largest connected white region
    sizes = ndimage.sum(white_mask, labeled, range(1, num + 1))
    largest_label = int(np.argmax(sizes) + 1)
    background_mask = labeled == largest_label

    # Convert background mask to float for feathering
    mask_float = background_mask.astype(float)

    # Apply a gentle Gaussian blur to feather the border
    if feather_radius > 0:
        mask_float = ndimage.gaussian_filter(mask_float, sigma=feather_radius)

    # Normalize blurred mask (0–1 range)
    mask_float = np.clip(mask_float, 0.0, 1.0)

    # Apply feathered transparency
    alpha = a.astype(float)
    alpha *= 1.0 - mask_float
    arr[..., 3] = alpha.astype(np.uint8)

    return Image.fromarray(arr)


def create_diagonal_gradient(
    size: tuple[int, int], start_color: str, end_color: str
) -> Image.Image:
    """
    Create a diagonal linear gradient image from start_color → end_color.
    Adds a soft white feather toward the bottom-left corner.
    """
    width, height = size
    base = np.zeros((height, width, 3), dtype=np.float32)

    # Coordinate grids
    x = np.linspace(0, 1, width)
    y = np.linspace(1, 0, height)
    xv, yv = np.meshgrid(x, y)

    # Main diagonal gradient (top-left → bottom-right)
    grad = (xv + yv) / 2

    # Feather mask for bottom-left corner
    white_mask = (1 - xv) * (1 - yv)
    white_mask = np.clip(white_mask, 0, 1)

    # Convert colors
    start_rgb = np.array(ImageColor.getrgb(start_color), dtype=np.float32)
    end_rgb = np.array(ImageColor.getrgb(end_color), dtype=np.float32)
    white = np.array([255, 255, 255], dtype=np.float32)

    # Blend main gradient
    for i in range(3):
        color_channel = start_rgb[i] * (1 - grad) + end_rgb[i] * grad
        # Feather in white toward bottom-left
        color_channel = color_channel * (1 - white_mask) + white[i] * white_mask
        base[..., i] = color_channel

    return Image.fromarray(np.uint8(base), mode="RGB").convert("RGBA")


# === IMAGE GENERATION ===
def generate_image(
    ebird_id: str,
    background: str,
    size: tuple[int, int],
    favorite: bool = False,
    exotic: bool = False,
    corner_radius: int = 40,
) -> Image.Image:
    """
    Generate an image with optional background color or local image
    and bird overlay (background auto-removed).
    """
    # Background: gradient, color, or local image
    if favorite and ebird_id:
        img = create_diagonal_gradient(size, "#ffffff", "#f8b600")  # white → yellow
    elif exotic and ebird_id:
        img = create_diagonal_gradient(size, "#ffffff", "#aaaaaa")  # white → red
    elif re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", background):
        img = Image.new("RGBA", size, color=background)
    else:
        try:
            background_path = ROOT_DIR / background
            bg = (
                Image.open(background_path)
                .convert("RGBA")
                .resize(size, Image.Resampling.LANCZOS)
            )
            img = bg
        except Exception as e:
            print(f"Error loading background image '{background}': {e}")
            img = Image.new("RGBA", size, color="black")

    # Add bird overlay if available
    if ebird_id:
        icons_path = DATA_DIR / "icons.json"
        try:
            with open(icons_path, "r", encoding="utf-8") as f:
                ebird_images = json.load(f)
        except FileNotFoundError:
            print(f"Error: icons.json not found at {icons_path}")
            return img.convert("RGB")

        asset_id = ebird_images.get(ebird_id)
        if asset_id:
            url = f"https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{asset_id}/640"
            local_icon = PROJECT_CACHE_DIR / "icons" / f"{ebird_id}.jpg"
            bird = Image.open(local_icon).convert("RGBA") if local_icon.exists() else fetch_image(url)
            if bird:
                bird = remove_largest_white_background(bird)
                bird.thumbnail((size[0] * 0.9, size[1] * 0.9), Image.Resampling.LANCZOS)

                # Center the bird
                bx = (size[0] - bird.width) // 2
                by = (size[1] - bird.height) // 2
                img.paste(bird, (bx, by), bird)

    # Apply rounded corners
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, *size], radius=corner_radius, fill=255)
    img.putalpha(mask)

    # Composite on black background and return RGB
    final = Image.new("RGBA", size, (0, 0, 0, 255))
    final.paste(img, (0, 0), img)
    return final.convert("RGB")


# === MAIN TEST ===
if __name__ == "__main__":
    img = generate_image(
        ebird_id="greegr",
        background="#ff0000",
        size=(288, 288),
        favorite=True,
    )
    img.show()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_DIR / "test_bird_image.png")
