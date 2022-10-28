import datetime
import time

import requests
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from api import secrets
from api.services.steammarketcrawler import SteamMarketCrawler
from api.services.untis import Untis
from api.util import db_utils, utils
from api.util.decorators import requires, optional
from api.util.telegram_bot import send_telegram_message
from api.util.utils import to_formatted_time, to_formatted_date, error


@csrf_exempt
@requires(permission=["telegram"], query_params=["message"])
def send_telegram_message_to_me(request, message):
    """Send a telegram message to my chat"""

    telegram_token: str = db_utils.get_store_item("telegram_token")
    telegram_chat_id = db_utils.get_store_item("telegram_my_chat_id", int)

    if not telegram_token or not telegram_chat_id:
        return utils.error(500, "Internal Server Error")

    send_telegram_message(telegram_token, telegram_chat_id, message)

    return utils.success()


@requires(permission="untis", query_params="key")
@optional(["webview", "day", "timeformat"])
def get_untis_timetable(request, key, webview="False", day=None, timeformat=None):
    try:
        try:
            webview: bool = True if webview.lower() == "true" else False
        except Exception as e:
            webview = False

        school_times = [("07:45:00", "09:15:00", False, 1),
                        ("09:15:00", "09:30:00", True, 1 / 6),
                        ("09:30:00", "11:00:00", False, 1),
                        ("11:00:00", "11:20:00", True, 2 / 9),
                        ("11:20:00", "12:50:00", False, 1),
                        ("12:50:00", "13:30:00", True, 4 / 9),
                        ("13:30:00", "15:00:00", False, 1),
                        ("15:00:00", "16:30:00", False, 1)]

        untis = Untis(secrets.UNTIS_CREDS)

        n = datetime.datetime.now()
        datetime_now_formatted = f'{to_formatted_time(n)} {to_formatted_date(n)}'

        custom_day = not not day
        # * Try to parse the date from the query string
        try:
            if day is not None:
                if timeformat is not None:
                    try:
                        day = datetime.datetime.strptime(day, timeformat).date()
                    except:
                        day = datetime.datetime.strptime(day, "%Y-%m-%d").date()

                else:
                    day = datetime.datetime.strptime(day, "%Y-%m-%d").date()

        except:
            day = None
        if day is None:
            day = datetime.date.today()

        today = datetime.date.today()
        monday = day - datetime.timedelta(days=day.weekday())
        friday = monday + datetime.timedelta(days=5)

        if monday == today - datetime.timedelta(days=today.weekday()) and custom_day:
            return HttpResponseRedirect(f"/untis/timetable?key={key}&webview=True")

        # * Get the timetable from the untis apiwrapper
        timetable_week = untis.get_timetable(day)

        context = {
            "timetable": timetable_week,
            "api_key": key,
            "day_formatted": f'{day.year}-{str(day.month).zfill(2)}-{str(day.day).zfill(2)}',
            "times": school_times,
            "today": f'{today.year}-{str(today.month).zfill(2)}-{str(today.day).zfill(2)}',
            "timestamp_today": time.time(),
            "dates": (monday, friday),
            "datetime_now_formatted": datetime_now_formatted,

        }
        if webview:
            return render(request, "api/timetable.html", context)
        else:
            return JsonResponse(context)
    except Exception as e:
        return error(500, str(e))


@requires(permission="discord-bot")
def restart_discord_bot_service(request):
    try:
        requests.post("http://127.0.0.1:777/exec-as-root", json={"command": ["systemctl", "restart", "discord-bot"]})
        return JsonResponse({"message": "success"})
    except Exception as e:
        return JsonResponse({"message": "failed", "details": e})


@requires(query_params="url")
@optional(query_params="filter")
def get_price_from_steam_market(request, url, filter=None):
    try:
        prices = SteamMarketCrawler.pricesFromMarketURL(url)

        if type(filter) == str:
            if filter.lower() in ["sell", "lowest_sell_order"]:
                return HttpResponse(prices.get("lowest_sell_order", ""))
            elif filter.lower() in ["buy", "highest_buy_order"]:
                return HttpResponse(prices.get("highest_buy_order", ""))

        return JsonResponse(prices)
    except ValueError:
        return JsonResponse({"error": "Invalid URL"})
