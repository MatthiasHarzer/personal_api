import json


def str_to_dict(string: str):
    """Converts a string to a dict. Returns {} if conversion fails"""
    try:
        return json.loads(string)
    except Exception:
        return {}
