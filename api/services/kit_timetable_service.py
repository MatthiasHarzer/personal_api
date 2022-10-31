from __future__ import annotations

import datetime
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Optional

from icalendar import Calendar
from icalendar.cal import Component

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

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)

type_map = {
    "ü": "exercise",
    "vü": "lecture",
    "v": "lecture",
    "tu": "tutorial",
}


@dataclass
class Event:
    """Represents a single event in the timetable."""
    start: datetime.datetime
    end: datetime.datetime
    summary: str
    location: str
    url: str
    recurring: bool = False

    @property
    def event_type(self) -> str:
        """Returns the type of the event."""
        for short, type_ in type_map.items():
            if f"({short})" in self.summary.lower():
                return type_
        return "other"

    def __dict__(self):
        return {
            "start": self.start.time(),
            "end": self.end.time(),
            "summary": self.summary,
            "location": self.location,
            "url": self.url,
            "type": self.event_type,
            "recurring": self.recurring,
        }

    @staticmethod
    def from_ical_event_if_valid(event: Component, current_week: list[datetime.datetime]) -> Optional[Event]:
        """
        Creates an Event from an icalendar event if it is valid.
        :param event: The icalendar event.
        :param current_week: A list containing all 7 datetime.datetimes from the current week.
        """
        start: datetime.datetime = event.get("dtstart").dt
        end: datetime.datetime = event.get("dtend").dt
        summary = event.get("summary")
        location = event.get("location")
        url = event.get("url")
        recurring = event.get("RRULE") is not None

        # check if the event is non recurring and in the current week
        if not recurring and start.date() not in [w.date() for w in current_week]:
            return None

        day = current_week[start.weekday()]  # the weekday of the event in the current week

        exceptions = event.get("exdate")

        # check if the event has exception dates and if an exception is in the current weeks day
        if exceptions:
            for exception in exceptions:
                for exc in exception.dts:
                    if exc.dt.date() == day.date():
                        return None

        return Event(
            start=datetime.datetime.combine(day, start.time()),
            end=datetime.datetime.combine(day, end.time()),
            summary=summary,
            location=location,
            url=url,
            recurring=recurring,
        )


@dataclass
class Timetable:
    """Represents the current timetable."""
    events: list[Event]
    week: list[datetime.datetime]

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
            "events": {i: [e.__dict__() for e in es] for i, es in self.events_by_weekday.items()},
            "class_times": CLASS_TIMES,
            "monday": self.week[0].date(),
            "friday": self.week[4].date(),
        }


def _get_timetable_file(url) -> str:
    """Downloads a file from the given url and saves it to the given file path."""
    id_ = url.split("/")[-1]

    file_path = f"{CACHE_DIR}/{id_}.ics"
    if os.path.isfile(file_path) and time.time() - os.path.getmtime(file_path) < FILE_MAX_AGE:
        return file_path

    urllib.request.urlretrieve(url, file_path)

    return file_path


def get_timetable(url: str = None, week_day: datetime.datetime = None) -> Timetable:
    """Returns the current timetable."""
    week_day = week_day or datetime.datetime.now()
    url = url or secrets.KIT_TIMETABLE_WEBCAL_URL

    monday = week_day - datetime.timedelta(days=week_day.weekday())
    week = [monday + datetime.timedelta(days=i) for i in range(7)]  # the current week

    with open(_get_timetable_file(url), "r") as f:
        cal: Calendar = Calendar.from_ical(f.read())

        events: list[Event] = []

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            e = Event.from_ical_event_if_valid(component, week)

            if e:
                events.append(e)

        return Timetable(events=events, week=week)
