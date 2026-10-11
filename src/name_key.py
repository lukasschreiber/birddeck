"""Validate the optional scientific name used by the scrolling plugin."""
def validate_scientific_name(value):
    if not isinstance(value, str) or len(value) > 200:
        raise ValueError('Scientific name must be text of at most 200 characters')
    return value.strip()
