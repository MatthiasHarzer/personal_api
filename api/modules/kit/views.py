import datetime
import re
import traceback
from typing import Optional

from django.http import JsonResponse

from api.services.kit import kit_timetable_service, kit_events_service
from api.util import utils, tc
from api.util.decorators import requires, optional


@requires(permission="kit")
@optional("day")
def get_kit_timetable(request, day=None):
    """Returns the timetable for the current day"""

    parsed_day: Optional[datetime.datetime] = None

    if day is not None:
        parsed_day = utils.parse_str_to_datetime(day)

        if parsed_day is None:
            return utils.error(400, "Invalid date format. Please use YYYY-MM-DD")

    timetable: kit_timetable_service.Timetable = kit_timetable_service.get_timetable(week_day=parsed_day)

    return JsonResponse(timetable.as_json())


@requires(permission="kit-public", query_params="url")
@optional("day")
def get_kit_timetable_public(request, url, day=None):
    # noinspection *
    kit_webcal_url_re = re.compile("^https?:\/\/campus\.kit\.edu\/sp\/webcal\/\w*")

    parsed_day: Optional[datetime.datetime] = None

    if day is not None:
        parsed_day = utils.parse_str_to_datetime(day)

        if parsed_day is None:
            return utils.error(400, "Invalid date format. Please use YYYY-MM-DD")

    if not kit_webcal_url_re.match(url):
        return utils.error(400, "Invalid URL")

    timetable: kit_timetable_service.Timetable = kit_timetable_service.get_timetable(url, week_day=parsed_day)

    return JsonResponse(timetable.as_json())


@requires(permission="kit-public", query_params=["day", "time"])
@optional(("type", tc.str_to_list), suffix="_")
def get_kit_events(request, day: str, time: str, type_: Optional[list[str]] = None):
    """Returns the events for the current day"""

    events = []

    try:
        events = kit_events_service.get_events(day, time, type_)
    except Exception as e:
        traceback.print_exc()
        # ignored
        pass

    return JsonResponse({
        "events": events
    })
