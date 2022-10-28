import base64
import datetime
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.util import db_utils, converter, utils
from api.util.decorators import requires, optional

def home(_):
    return JsonResponse({"message": "Hello world!"})

def get_arduino_formatted_time(request):
    """Returns the current time in the format that the Arduino expects (dict-like)"""
    # now = get_korean()
    now = datetime.datetime.now()
    return JsonResponse({
        "hours": now.hour,
        "minutes": now.minute,
        "seconds": now.second,
        "day": now.day,
        "month": now.month,
        "year": now.year
    })


def get_arduino_clock_settings(request):
    """Returns the current clock settings in the format that the Arduino expects (dict-like)"""
    settings = db_utils.get_store_item("arduino_clock_settings", converter.str_to_dict)
    if settings:
        return JsonResponse(settings)
    return utils.error(500, "crash")


@csrf_exempt
@requires(permission=["arduino_clock"], query_params=["sdata"])
@optional(["format"], prefix="d")
def set_arduino_clock_settings(request, sdata, dformat=None):
    """Sets the clock settings on the Arduino"""

    settings_data = {}

    if not sdata:
        return utils.error(401, {"missing": ["sdata"]})

    success = False

    if dformat == "json" or not dformat:  # Format is optional when sending jsonString
        settings_data = converter.str_to_dict(sdata)
        try:
            settings_data: dict = json.loads(sdata)
            success = True
        except Exception as e:
            print(e)

    if dformat == "b64" or len(settings_data.items()) <= 0:
        try:
            settings_data: dict = json.loads(base64.b64decode(
                sdata.encode('utf-8')).decode('utf-8'))
        except Exception as e:
            settings_data = {}

    if len(settings_data.items()) <= 0:
        return utils.error(401, {"invalid": ["sdata"]})

    settings = db_utils.get_store_item("arduino_clock_settings", converter.str_to_dict) or {}

    for skey, svalue in settings_data.items():
        settings[skey] = svalue

    db_utils.set_store_item("arduino_clock_settings", json.dumps(settings))

    # * Inform websocket clients
    # WebsocketServer.update("arduino_clock_settings", to_b64(settings))
    db_utils.update_scope("arduino_clock_settings", settings)

    return utils.success()


# For single settings update
@csrf_exempt
@requires(permission=["arduino_clock"], query_params=["skey", "svalue"])
def set_single_arduino_clock_setting(request, skey, svalue):
    """Sets a single clock setting on the Arduino"""

    if not skey or not svalue:
        return utils.error(401, {"missing_one_or_more": ["skey", "svalue"]})

    settings = db_utils.get_store_item("arduino_clock_settings", converter.str_to_dict) or {}

    settings[skey] = svalue

    db_utils.set_store_item("arduino_clock_settings", json.dumps(settings))

    # * Inform websocket clients
    # WebsocketServer.update("arduino_clock_settings", to_b64(settings))
    db_utils.update_scope("arduino_clock_settings", settings)

    return utils.success()
