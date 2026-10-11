"""Render a quiet, centered bird name key for the detail page."""
from functools import lru_cache
from math import ceil
from PIL import Image, ImageDraw, ImageFont


def validate_scientific_name(value):
    if not isinstance(value, str) or len(value) > 200:
        raise ValueError('Scientific name must be text of at most 200 characters')
    return value.strip()


@lru_cache(maxsize=64)
def font(size, italic=False):
    candidates = (
        ('ariali.ttf' if italic else 'arial.ttf'),
        ('DejaVuSans-Oblique.ttf' if italic else 'DejaVuSans.ttf'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf' if italic
         else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def fit_lines(text, draw, max_size, italic=False, max_height=124):
    for size in range(max_size, 15, -1):
        face = font(size, italic)
        lines, line = [], ''
        for word in text.split():
            candidate = f'{line} {word}'.strip()
            if draw.textlength(candidate, font=face) <= 248:
                line = candidate
                continue
            if line:
                lines.append(line)
            # Balance a long compound name across lines instead of leaving
            # only a few letters on the last line at the physical key size.
            chunks = [word]
            for count in range(2, len(word) + 1):
                if all(draw.textlength(chunk, font=face) <= 248 for chunk in chunks):
                    break
                length = ceil(len(word) / count)
                chunks = [word[i:i + length] for i in range(0, len(word), length)]
            lines.extend(chunks[:-1])
            line = chunks[-1]
        if line:
            lines.append(line)
        if len(lines) <= 3 and len(lines) * (size + 5) <= max_height:
            return lines, face, size + 5
    if len(lines) > 3:
        lines = lines[:3]
        while lines[-1] and draw.textlength(lines[-1] + '…', font=face) > 248:
            lines[-1] = lines[-1][:-1]
        lines[-1] += '…'
    return lines, face, size + 5


def render_name_key(title, scientific_name=''):
    scientific_name = validate_scientific_name(scientific_name)
    # Match the webapp: only remove hyphens followed by lowercase letters.
    title = ''.join(c for i, c in enumerate(title)
                    if not (c == '-' and i + 1 < len(title) and title[i + 1].islower()))
    canvas = Image.new('RGB', (288, 288), '#000000')
    draw = ImageDraw.Draw(canvas)
    common, common_font, common_height = fit_lines(title, draw, 56, max_height=124 if scientific_name else 240)
    scientific, scientific_font, scientific_height = fit_lines(scientific_name, draw, 44, italic=True, max_height=100)
    gap = 18 if scientific else 0
    height = len(common) * common_height + gap + len(scientific) * scientific_height
    y = (288 - height) / 2
    for line in common:
        draw.text((144, y), line, font=common_font, fill='#ffffff', anchor='mt')
        y += common_height
    y += gap
    for line in scientific:
        draw.text((144, y), line, font=scientific_font, fill='#d0d4d8', anchor='mt')
        y += scientific_height
    return canvas
