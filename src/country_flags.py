import json
from paths import DATA_DIR, ROOT_DIR

COUNTRIES = json.loads((DATA_DIR / 'countries.json').read_text(encoding='utf-8'))


def validate_country(value):
    if not isinstance(value, str):
        raise ValueError('Choose a two-letter country code')
    code = value.strip().upper()
    if code and code not in COUNTRIES:
        raise ValueError('Unknown country code')
    return code


def flag_path(code):
    return ROOT_DIR / 'assets' / 'flags' / f'{validate_country(code)}.png'
