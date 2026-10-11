from PIL import Image


def image_size(profile):
    value = profile.get('image_size', 72)
    if type(value) is not int or not 16 <= value <= 1024:
        raise ValueError('profile.image_size must be an integer between 16 and 1024 pixels')
    return value


def save_key_image(image, path, pixels):
    image = image.resize((pixels, pixels), Image.Resampling.LANCZOS)
    image.save(path, format='PNG', optimize=True)
