import datetime
import os
import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from api.models import KITRoomAddressCache
from api.services.kit import consts
from api.services.kit.consts import CLASS_TIMES_AS_STRINGS_DICT, KIT_EXTENDED_SEARCH_HEADERS, KIT_EVENT_ID_REGEX, \
    CACHE_DIR_EVENTS, CACHE_DIR_ROOMS

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
class KITRoom:
    """Represents a room"""
    name: Optional[str] = None
    gguid: Optional[str] = None
    cms_map_link: Optional[str] = None
    google_maps_link: Optional[str] = None

    def as_json(self):
        return {
            "name": self.name,
            "gguid": self.gguid,
            "cms_map_link": self.cms_map_link,
            "google_maps_link": self.google_maps_link,
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
    room: Optional[KITRoom] = None
    time: Optional[str] = None

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
            "room": self.room.as_json() if self.room is not None else KITRoom().as_json(),
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


def _get_raw_room_data_from_cached_or_server(gguid: str, force: bool = False) -> str:
    """Returns the raw room data from the server or the cache"""
    file_name = f"{gguid}.html"
    file_path = os.path.join(CACHE_DIR_ROOMS, file_name)
    if os.path.exists(file_path) and not force:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        req = requests.get(f"https://campus.kit.edu/sp/campus/all/room.asp?gguid={gguid}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(req.text.encode("utf-8").decode("utf-8"))

        return req.text


def _get_room_google_maps_link_by_gguid(gguid: str) -> Optional[str]:
    raw_room_data = _get_raw_room_data_from_cached_or_server(gguid)
    gm_matches = re.findall(consts.GOOGLE_MAPS_URL_REGEX, raw_room_data)

    google_maps_link = None
    if len(gm_matches) > 0:
        google_maps_link = f"{gm_matches[0]}&z=17"
    return google_maps_link


def _get_room_by_tag(tag: BeautifulSoup) -> KITRoom:
    """Returns the room by the given tag"""
    room_name = tag.text.strip()
    # room_gguid = room_link.split("gguid=")[1]

    room_href = tag.get("href", "")

    room_gguid_matched = re.findall(consts.KIT_ROOM_GGUID_REGEX, room_href)

    room_gguid = None
    kit_map_link = None
    building_number = None

    if len(room_gguid_matched) > 0:
        room_gguid = room_gguid_matched[0]

    building_matches: list[tuple[str]] = re.findall(consts.KIT_BUILDING_NUMBER_REGEX, room_name)

    if len(building_matches) > 0:
        if len(building_matches[0]) > 1:
            building_number = building_matches[0][1]
            kit_map_link = f"https://www.kit.edu/campusplan/?id={building_number}"

    google_maps_link = None

    if building_number is not None:
        try:
            existing = KITRoomAddressCache.objects.get(building_id=building_number)
            google_maps_link = existing.google_maps_link
        except KITRoomAddressCache.DoesNotExist:
            google_maps_link = _get_room_google_maps_link_by_gguid(room_gguid)

            if google_maps_link is not None:
                KITRoomAddressCache(building_id=building_number, google_maps_link=google_maps_link).save()
    else:
        google_maps_link = _get_room_google_maps_link_by_gguid(room_gguid)

    return KITRoom(
        name=room_name,
        gguid=room_gguid,
        cms_map_link=kit_map_link,
        google_maps_link=google_maps_link,
    )


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

            current_event.room = _get_room_by_tag(room_tag)

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
