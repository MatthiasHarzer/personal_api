import datetime
import os
import re

from personal_api import settings

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
# [f"{x[0].strftime('%H:%M')} - {x[1].strftime('%H:%M')}" for x in CLASS_TIMES]
CLASS_TIMES_AS_STRINGS_DICT = {
    k.strftime("%H:%M"): v.strftime("%H:%M") for k, v, *_ in CLASS_TIMES
}

BASE_DIR = settings.BASE_DIR
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CACHE_DIR_TIMETABLE = os.path.join(CACHE_DIR, "timetable")
CACHE_DIR_EVENTS = os.path.join(CACHE_DIR, "events")

if not os.path.exists(CACHE_DIR_TIMETABLE):
    os.makedirs(CACHE_DIR_TIMETABLE, exist_ok=True)
if not os.path.exists(CACHE_DIR_EVENTS):
    os.makedirs(CACHE_DIR_EVENTS, exist_ok=True)


KIT_EXTENDED_SEARCH_HEADERS = {'authority': 'campus.kit.edu', 'method': 'POST',
                               'path': '/sp/campus/all/extendedSearch.asp', 'scheme': 'https',
                               'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                               'accept-encoding': 'gzip, deflate, br',
                               'accept-language': 'en,en-US;q=0.9,de;q=0.8,da;q=0.7,zh-CN;q=0.6,zh;q=0.5,es;q=0.4',
                               'cache-control': 'max-age=0', 'content-length': '452',
                               'content-type': 'application/x-www-form-urlencoded',
                               'cookie': 'session-campus-prod-sp=AWTAQSQRENGKPJNCGGLNAHJHCLCEPAMC',
                               'origin': 'https://campus.kit.edu',
                               'referer': 'https://campus.kit.edu/sp/campus/all/extendedSearch.asp',
                               'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                               'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'iframe',
                               'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'same-origin', 'sec-fetch-user': '?1',
                               'upgrade-insecure-requests': '1',
                               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64;x64) AppleWebKit / 537.36(KHTML, like Gecko) Chrome / 107.0.0.0 Safari / 537.36'}
KIT_EVENT_ID_REGEX = re.compile("^0x\w*", re.IGNORECASE)
