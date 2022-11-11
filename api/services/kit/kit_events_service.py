import os
import urllib.parse
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from api.services.kit.consts import CLASS_TIMES_AS_STRINGS_DICT, KIT_EXTENDED_SEARCH_HEADERS, KIT_EVENT_ID_REGEX

BASE_URL = "https://campus.kit.edu/sp/campus/all/extendedSearch.asp"
RAW_FORM_DATA = "search=Suchen&tguid=0xB7532209C5264C53A99D9128A9F9A321&eventcoursenumber=&eventtitle=&eventtype=Vorlesung+%28V%29&eventformat=&eventlanguage=&appointmentperiod=&appointmentweekday=&appointmentdate=11.11.2022&appointmenttimestart=14%3A00&appointmenttimeend=15%3A30&product=%7B%7D&module=%7B%7D&brick=%7B%7D&audience=%7B%7D&field=%7B%7D&unit=%7B%7D&room=%7B%7D&lect=%7B%7D"
PARSED_FORM_DATA = {
    k: v for k, v in [x.split("=") for x in RAW_FORM_DATA.split("&")]
}


# print(CLASS_TIMES_AS_STRINGS_DICT)


@dataclass
class KITEvent:
    id: str
    title: str
    type: str
    lecturer: str
    format: str
    link: str
    day: Optional[str] = None
    room: Optional[str] = None
    # time: str

    def as_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "lecturer": self.lecturer,
            "format": self.format,
            "link": self.link,
            "day": self.day,
            "room": self.room,
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
    file_name = f"{day}_{time}.html"
    if os.path.exists(file_name) and not force:
        with open(file_name, "r") as f:
            return f.read()
    else:
        form_data = _build_form_data(day, time)

        req = requests.post(BASE_URL, data=form_data, headers=KIT_EXTENDED_SEARCH_HEADERS)

        with open(file_name, "w") as f:
            f.write(req.text)

        return req.text


def _parse_raw_data(raw_data: str) -> list[KITEvent]:
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
            title = row_data[2].find("a").text
            host = row_data[3].text
            event_type = row_data[4].text
            event_format = row_data[6].text

            current_event = KITEvent(
                id=row_id,
                title=title,
                type=event_type,
                lecturer=host,
                # day=day,
                format=event_format,
                # time=time,
                link=f"https://campus.kit.edu/sp/campus/all/event.asp?gguid={row_id}",
            )
            events.append(current_event)
            # events[current_event_id] = {
            #     "title": title,
            #     "host": host,
            #     "event_type": event_type,
            #     "event_format": event_format,
            # }
        elif current_event is not None:
            date_room = row_data[-1]
            if date := date_room.find("span", {"class": "date"}):
                current_event.day = date.text
            if room := date_room.find("span", {"class": "room"}):
                current_event.room = room.text
            # date = date_room.find("span", {"class": "date"}).text
            # room = date_room.find("span", {"class": "room"}).text

            # current_event.room = room
            # current_event.day = date

    return events


def get_events(day: str, time: str) -> list:
    """Returns a list of all events of the given type"""

    raw_html = _get_raw_data_from_cached_or_server(day, time)

    data = _parse_raw_data(raw_html)

    # print(data)

    return [x.as_json() for x in data]
