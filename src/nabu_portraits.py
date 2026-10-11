"""Validate optional NABU portrait links from configuration and the editor."""
import re
from urllib.parse import urlsplit


def validate_nabu_url(value):
    if not isinstance(value, str):
        raise ValueError('NABU portrait link must be a URL')
    value = value.strip()
    if not value:
        return ''
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or parsed.netloc != 'www.nabu.de'
            or not re.fullmatch(r'/tiere-und-pflanzen/voegel/portraets/[A-Za-z0-9-]+/', parsed.path)
            or parsed.query or parsed.fragment):
        raise ValueError('Choose an HTTPS NABU bird portrait link')
    return value
