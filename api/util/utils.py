import base64
import datetime
import json
import random
import string
import time
from typing import Any, Optional

from django.http import JsonResponse


def to_formatted_time(datetime_: datetime.datetime) -> str:
    """Converts a datetime.datetime object to a formatted time string (%H:%M:%S)"""
    return datetime_.strftime("%H:%M:%S")


def to_formatted_date(datetime_: datetime.datetime) -> str:
    """Converts a datetime.datetime object to a formatted date string (%Y-%m-%d)"""
    return datetime_.strftime("%Y-%m-%d")


def str_to_date(date: str) -> datetime.datetime:
    """Converts a date string in format %Y-%m-%d to datetime.datetime object"""
    return datetime.datetime.strptime(date, "%Y-%m-%d")


def str_to_datetime(datetime_: str) -> datetime.datetime:
    """Converts a datetime string in format %H:%M:%S to datetime.datetime object"""
    return datetime.datetime.strptime(datetime_, "%H:%M:%S")


def delay(secs: int, func: callable):
    """Delays the execution of a function by a given amount of seconds"""
    time.sleep(secs)
    func()


def dict_to_b64(data: dict) -> str:
    """Converts a dict to base64 string"""
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()


def b64_to_dict(b64_string: str) -> dict:
    """Converts a base64 string to dict. Returns {} if conversion fails"""
    try:
        return json.loads(base64.b64decode(b64_string.encode('utf-8')).decode('utf-8'))
    except Exception:
        return {}


def random_string(length: int = 30) -> str:
    """Returns a random string with the given length"""
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


def error(code: int, message: Any):
    """Template for error-JsonResponse"""
    return JsonResponse({"error": {"code": code, "message": message}})


def success():
    """Template for success-JsonResponse"""
    return JsonResponse({"success": True})


def parse_str_to_datetime(datetime_: str) -> Optional[datetime.datetime]:
    """Converts a datetime string in format %H:%M:%S to datetime.datetime object"""
    try:
        return datetime.datetime.strptime(datetime_, "%Y-%m-%d")
    except ValueError:
        return None


def date_is_in_current_week(date: datetime.datetime) -> bool:
    """Checks if the given date is in the current week"""
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    friday = monday + datetime.timedelta(days=5)
    return monday <= date.date() <= friday
