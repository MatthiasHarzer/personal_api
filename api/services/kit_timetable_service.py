import datetime
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Optional

from icalendar import Calendar

from api import secrets
from personal_api import settings

FILE_MAX_AGE = 60 * 60 * 24  # 1 days
CLASS_TIMES = [
    (datetime.time(8, 0), datetime.time(9, 30), False, 1),
    (datetime.time(9, 30), datetime.time(9, 45), True, 1 / 6),
    (datetime.time(9, 45), datetime.time(11, 15), False, 1),
    (datetime.time(11, 15), datetime.time(11, 30), True, 1 / 6),
    (datetime.time(11, 30), datetime.time(13, 0), False, 1),
    (datetime.time(13, 0), datetime.time(14, 0), True, 2 / 3),
    (datetime.time(14, 0), datetime.time(15, 30), False, 1),
    (datetime.time(15, 30), datetime.time(15, 45), True, 1 / 6),
    (datetime.time(15, 45), datetime.time(17, 15), False, 1),
    (datetime.time(17, 15), datetime.time(17, 30), True, 1 / 6),
    (datetime.time(17, 30), datetime.time(19, 0), False, 1),
]

BASE_DIR = settings.BASE_DIR
CACHE_DIR = os.path.join(BASE_DIR, "cache", "timetable")


@dataclass
class Event:
    """Represents a single event in the timetable."""
    start: datetime.datetime
    end: datetime.datetime
    summary: str
    location: str
    url: str

    def __dict__(self):
        return {
            "start": self.start.time(),
            "end": self.end.time(),
            "summary": self.summary,
            "location": self.location,
            "url": self.url,
        }


@dataclass
class Timetable:
    """Represents the current timetable."""
    events: list[Event]

    @property
    def events_by_weekday(self) -> dict[int, list[Event]]:
        """Returns a dictionary of events, where the key is the weekday (0 = Monday, 6 = Sunday)"""
        events_by_weekday = {i: [] for i in range(7)}
        for event in self.events:
            events_by_weekday[event.start.weekday()].append(event)
        return events_by_weekday

    def __post_init__(self):
        self.events.sort(key=lambda e: e.start)

    def as_json(self):
        return {
            "events": {i: [e.__dict__() for e in es] for i, es in self.events_by_weekday.items() }
        }


def get_timetable_file(url, file_type: str = "ics") -> str:
    """Downloads a file from the given url and saves it to the given file path."""
    id_ = url.split("/")[-1]

    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    file_path = f"{CACHE_DIR}/{id_}.{file_type}"
    if os.path.isfile(file_path) and time.time() - os.path.getmtime(file_path) < FILE_MAX_AGE:
        return file_path

    urllib.request.urlretrieve(url, file_path)

    return file_path


def get_timetable(url: str = None) -> Timetable:
    """Returns the current timetable."""
    url = url or secrets.KIT_TIMETABLE_WEBCAL_URL
    with open(get_timetable_file(url, "ics"), "r") as f:
        cal: Calendar = Calendar.from_ical(f.read())

        events: list[Event] = []

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            events.append(Event(
                start=component.get("dtstart").dt,
                end=component.get("dtend").dt,
                summary=component.get("summary"),
                location=component.get("location"),
                url=component.get("url"),
            ))

        return Timetable(events=events)
