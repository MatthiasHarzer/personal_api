import json
from typing import Callable, Optional

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


def str_to_list(str_: str, separator: str = ",", type_: Optional[TypeConverter] = None) -> list:
    """
    Converts a string to a list of values.

    :param str_: The string to convert.
    :param separator: The separator used to split the string.
    :param type_: The type of the values in the list. Can be any callable function with a single parameter.
    """
    type_ = type_ if type_ is not None else lambda x: x

    return [type_(s.strip()) for s in str_.split(separator)]
