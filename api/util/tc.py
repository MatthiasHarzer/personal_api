import json
from typing import Callable

TypeConverter = Callable[[str], any]


def str_to_dict(string: str) -> dict:
    """Converts a string to a dict. Returns {} if conversion fails"""
    try:
        return json.loads(string)
    except Exception:
        return {}


def str_to_bool(s: str) -> bool:
    """Converts a string to a boolean"""
    return s.lower() in ("yes", "true", "t", "1")
