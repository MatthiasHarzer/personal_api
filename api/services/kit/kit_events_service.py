import datetime
import os
import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from api.services.kit import consts
from api.services.kit.consts import CLASS_TIMES_AS_STRINGS_DICT, KIT_EXTENDED_SEARCH_HEADERS, KIT_EVENT_ID_REGEX, \
    CACHE_DIR_EVENTS

BASE_URL = "https://campus.kit.edu/sp/campus/all/extendedSearch.asp"
RAW_FORM_DATA = "search=Suchen&tguid=0xB7532209C5264C53A99D9128A9F9A321&eventcoursenumber=&eventtitle=&eventtype=Vorlesung+%28V%29&eventformat=&eventlanguage=&appointmentperiod=&appointmentweekday=&appointmentdate=11.11.2022&appointmenttimestart=14%3A00&appointmenttimeend=15%3A30&product=%7B%7D&module=%7B%7D&brick=%7B%7D&audience=%7B%7D&field=%7B%7D&unit=%7B%7D&room=%7B%7D&lect=%7B%7D"
PARSED_FORM_DATA = {
    k: v for k, v in [x.split("=") for x in RAW_FORM_DATA.split("&")]
}

# print(CLASS_TIMES_AS_STRINGS_DICT)
EVENT_TYPE_MAPPING = {
    "V": "Vorlesung",
    "Ü": "Übung",
    "P": "Praktikum",
    "S": "Seminar",
    "TU": "Tutorium",
}


@dataclass
class KITEvent:
    id: str
    title: str
    type: str
    type_short: str
    lecturer: str
    format: str
    link: str
    time: Optional[str] = None
    room: Optional[str] = None
    room_link: Optional[str] = None

    # time: str

    def as_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "lecturer": self.lecturer,
            "format": self.format,
            "link": self.link,
            "time": self.time,
            "room": self.room,
            "room_link": self.room_link,
            # "time": self.time
        }


def _build_form_data(day: str, time: str) -> str:
    """Builds the form data for the request"""
    start_time = time
    end_time = CLASS_TIMES_AS_STRINGS_DICT[time]

    data = PARSED_FORM_DATA.copy()

    data["appointmenttimestart"] = start_time
    data["appointmenttimeend"] = end_time
    data["appointmentdate"] = day

    as_string = "&".join([f"{k}={urllib.parse.quote_plus(v)}" for k, v in data.items()])

    return as_string


def _get_raw_data_from_cached_or_server(day: str, time: str, force: bool = False) -> str:
    """Returns the raw data from the server or the cache"""
    file_name = f"{day}_{time.replace(':', '.')}.html"
    file_path = os.path.join(CACHE_DIR_EVENTS, file_name)
    if os.path.exists(file_path) and not force:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        form_data = _build_form_data(day, time)

        req = requests.post(BASE_URL, data=form_data, headers=KIT_EXTENDED_SEARCH_HEADERS)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(req.text.encode("utf-8").decode("utf-8"))

        return req.text


def _parse_raw_data(raw_data: str, day_short: str, time: str, event_types: Optional[list[str]] = None) -> list[
    KITEvent]:
    """Parses the raw data from the request"""
    soup = BeautifulSoup(raw_data, "html.parser")

    table_content = soup \
        .find("table", {"id": "EVENTLIST"}) \
        .find("tbody", {"class": "tablecontent"})

    rows = table_content.find_all("tr")
    current_event: Optional[KITEvent] = None

    events: list[KITEvent] = []

    for row in rows:
        row_data = row.find_all("td")
        row_id = row.get("id")

        # print(row_id)

        if row_id and KIT_EVENT_ID_REGEX.match(row_id):
            title: str = row_data[2].find("a").text
            host: str = row_data[3].text
            event_type: str = row_data[4].text
            event_type_short: str = row_data[5].text.encode("utf-8", "ignore").decode("utf-8")
            event_format: str = row_data[6].text

            if event_types is not None and event_type_short.lower() not in event_types:
                continue

            current_event = KITEvent(
                id=row_id,
                title=title,
                type=event_type,
                type_short=event_type_short,
                lecturer=host,
                # day=day,
                format=event_format,
                time=time,
                link=f"https://campus.kit.edu/sp/campus/all/event.asp?gguid={row_id}",
            )
            events.append(current_event)
            # print(f"\n{row_id} {event_type}", end="")
            # events[current_event_id] = {
            #     "title": title,
            #     "host": host,
            #     "event_type": event_type,
            #     "event_format": event_format,
            # }
        elif current_event is not None:
            date_room = row_data[-1]

            date_tags = date_room.select(".date")
            room_tags = date_room.select(".room")
            # print(date_tags)

            # Only add the event if it is on the given day
            if len(date_tags) <= 0:
                continue
            #
            date_text = date_tags[0].text
            if not date_text.lower().startswith(day_short.lower()):
                continue

            if len(room_tags) <= 0:
                continue

            room_tag = room_tags[0]

            matches: list[tuple[str]] = re.findall(consts.KIT_BUILDING_NUMBER_REGEX, str(room_tag.text))

            if len(matches) > 0:
                if len(matches[0]) > 1:
                    building_number = matches[0][1]
                    current_event.room_link = f"https://www.kit.edu/campusplan/?id={building_number}"

            current_event.room = room_tag.text

    return events


def _get_day_short(day: str) -> str:
    """Returns the short day name"""
    date = datetime.datetime.strptime(day, "%d.%m.%Y")
    return [
        "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"
    ][date.weekday()]


def get_events(day: str, time: str, event_types_short: Optional[list[str]] = None) -> list:
    """Returns a list of all events of the given type"""

    raw_html = _get_raw_data_from_cached_or_server(day, time)
    short_day = _get_day_short(day)

    event_types_short = [str(e).lower() for e in event_types_short if
                         e is not None] if event_types_short is not None else None

    t = f"{time} - {CLASS_TIMES_AS_STRINGS_DICT[time]}"

    data = _parse_raw_data(raw_html, short_day, t, event_types_short)

    return [x.as_json() for x in data]
