import datetime
import json
from typing import Any, Optional

import webuntis

from api.util import db_utils, tc
from api.util.utils import to_formatted_date, to_formatted_time, str_to_date

start_times = ["07:45:00", "09:15:00", "09:30:00", "11:00:00", "11:20:00", "12:50:00", "13:30:00", "15:00:00"]
end_times = {"07:45:00": "09:15:00", "09:15:00": "09:30:00", "09:30:00": "11:00:00", "11:00:00": "11:20:00",
             "11:20:00": "12:50:00", "12:50:00": "13:30:00", "13:30:00": "15:00:00",
             "15:00:00": "16:30:00"}
break_times = [
    ("09:15:00", "09:30:00"),
    ("11:00:00", "11:20:00"),
    ("12:50:00", "13:30:00"),
]
subject_duration = 1.5
week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def start_to_end_time(datetime_: datetime.datetime) -> datetime.datetime:
    str_ = datetime_.strftime("%H:%M:%S")
    end = end_times.get(str_, str_)
    time = datetime.datetime.strptime(end, "%H:%M:%S")
    return datetime_.replace(hour=time.hour, minute=time.minute, second=time.second)


def date_plus_time_to_ts(datetime_: datetime.datetime, time_: str) -> float:
    time = datetime.datetime.strptime(time_, "%H:%M:%S")
    datetime_ = datetime_.replace(hour=time.hour, minute=time.minute, second=time.second)
    return datetime.datetime.timestamp(datetime_)


def stringify_holidays(dict_list: list[dict]) -> str:
    retval = []
    for item in dict_list:
        r = {}
        for k, v in item.items():
            # print(k, v)
            if type(v) == datetime.datetime:
                r[k] = to_formatted_date(v)
            else:
                r[k] = v
        retval.append(r)
    return str(json.dumps({"data": retval}))


def parse_holidays(holidays: dict) -> list[dict]:
    holidays: list[dict] = holidays.get("data", [])

    for h in holidays:
        h["start"] = str_to_date(h["start"])
        h["end"] = str_to_date(h["end"])
    return holidays


def timestamp(dt: datetime.datetime) -> float:
    return datetime.datetime.timestamp(dt)


def date_to_datetime(
        dt: datetime.date,
        hour: Optional[int] = 0,
        minute: Optional[int] = 0,
        second: Optional[int] = 0) -> datetime:
    return datetime.datetime(dt.year, dt.month, dt.day, hour, minute, second)


class TimetableBuilder:
    all_ = []

    # * Timestamp in s or ms (???) of given period
    @property
    def timestamp(self):
        return datetime.datetime.timestamp(self.datetime_)

    # * ..
    def __init__(self, datetime_, initial_subject):
        self.datetime_: datetime.datetime = datetime_
        self.subjects: list[dict] = [initial_subject]

    def __str__(self):
        return f'{to_formatted_date(self.datetime_)} {to_formatted_time(self.datetime_)} {self.timestamp}: {self.subjects}'

    def __add(self, subject):
        self.subjects.append(subject)

    @staticmethod
    def clear():
        TimetableBuilder.all_ = []

    # ! Add a subject with given datetime. If datetime already exists, add su to existing obj
    @classmethod
    def add_subject(cls, datetime_, subject_info):
        for p in TimetableBuilder.all_:
            if p.datetime_ == datetime_:
                p.__add(subject_info)
                break
        else:
            TimetableBuilder.all_.append(cls(datetime_, subject_info))

    # ! Return a formatted representation of the time table
    @classmethod
    def formatted(cls, monday: datetime.datetime, holidays: list[dict] = None) -> list[dict[str, Any]]:
        holidays = holidays if holidays is not None else []
        # * Sort periods by timestamp
        all_sorted: list[cls] = sorted(TimetableBuilder.all_, key=lambda p: p.timestamp)

        # print("....")
        # for s in all_sorted:
        #     print(str(s))
        # print(".....")

        # * Prepare return value
        retval = []

        # * Prepare day info
        for r_i in range(5):
            d = monday + datetime.timedelta(days=r_i)
            retval.append({
                "date": d,
                "day_formatted": f'{d.year}-{str(d.month).zfill(2)}-{str(d.day).zfill(2)}',
                "day_end_ts": timestamp(date_to_datetime(d, hour=18)),
                "day_start_ts": timestamp(date_to_datetime(d, hour=7, minute=45)),
                "pos": r_i,
                "week_day": week_days[r_i],
                "periods": [],
                "at_home": "",
                "is_holiday": False
            })

        time_counter = 0

        day_periods = []

        day_pos = 0
        last_day_pos = 0

        if len(all_sorted) > 0:
            last_official_subject_time = all_sorted[0].datetime_
            last_day = to_formatted_date(all_sorted[0].datetime_)
            for period in all_sorted:
                period: cls = period

                day = to_formatted_date(period.datetime_)

                # print(day, last_day, day!=last_day, str(period))

                if day != last_day:
                    athtime1 = start_to_end_time(last_official_subject_time) + datetime.timedelta(minutes=30)
                    athtime2 = athtime1 + datetime.timedelta(minutes=30)

                    retval[day_pos]["at_home"] = f'{to_formatted_time(athtime1)} - {to_formatted_time(athtime2)}'
                    retval[day_pos]["periods"] = day_periods.copy()

                    # print(day_pos, day_periods)

                    day_periods.clear()

                    day_pos = period.datetime_.isoweekday() - 1

                    time_counter = 0

                free = True
                for s in period.subjects:
                    if s.get("code", "") != "cancelled":
                        free = False
                if not free:
                    last_official_subject_time = period.datetime_

                # if to_formatted_time(period.datetime_) in [t[0] for t in break_times]:
                #     day_periods.

                while start_times[time_counter] != to_formatted_time(period.datetime_) and time_counter < len(
                        start_times):
                    # print(day, to_formatted_time(period.datetime_), start_times[time_counter], time_counter)
                    time = start_times[time_counter]
                    start_ts = date_plus_time_to_ts(period.datetime_, time)
                    end_ts = date_plus_time_to_ts(period.datetime_, end_times[time])

                    diff = (end_ts - start_ts)
                    hour_diff = diff / (60*60)
                    # print(time, hour_diff / 1.5)


                    # print(time, timestamp(period.datetime_), date_plus_time_to_ts(period.datetime_, time))
                    day_periods.append({
                        "start_time": time,
                        "end_time": end_times[time],
                        "timestamp": timestamp(start_to_end_time(period.datetime_)),
                        "ts_start": date_plus_time_to_ts(period.datetime_, time),
                        "ts_end": date_plus_time_to_ts(period.datetime_, end_times[time]),
                        "subjects": [],
                        "is_break": start_times[time_counter] in [t[0] for t in break_times],
                        "duration": hour_diff / 1.5
                    })
                    time_counter += 1

                day_periods.append({
                    "start_time": to_formatted_time(period.datetime_),
                    "end_time": end_times.get(to_formatted_time(period.datetime_),
                                              to_formatted_time(period.datetime_)),
                    "timestamp": timestamp(start_to_end_time(period.datetime_)),
                    "ts_start": timestamp(period.datetime_),
                    "ts_end": timestamp(start_to_end_time(period.datetime_)),
                    "subjects": sorted([s or "" for s in period.subjects], key=lambda x: x.get("code", "") or ""),
                    "is_break": False,
                    "duration": 1
                })
                last_day = day
                time_counter += 1
                last_day_pos = period.datetime_.isoweekday() - 1

            athtime1 = start_to_end_time(last_official_subject_time) + datetime.timedelta(minutes=30)
            athtime2 = athtime1 + datetime.timedelta(minutes=30)

            retval[last_day_pos]["at_home"] = f'{to_formatted_time(athtime1)} - {to_formatted_time(athtime2)}'
            retval[day_pos]["periods"] = day_periods.copy()

        if holidays and monday is not None:
            for day_index in range(len(retval)):

                day: datetime.datetime = date_to_datetime(monday + datetime.timedelta(days=day_index))

                for holiday in holidays:
                    start: datetime.datetime = holiday.get("start", None)
                    end: datetime.datetime = holiday.get("end", None)

                    # print(start, end)

                    if end and start:
                        # print(timestamp(day), timestamp(start), timestamp(end), (day >= start, timestamp(day) >= timestamp(start)), )
                        if start <= day <= end:
                            retval[day_index]["is_holiday"] = True
                            retval[day_index]["holiday"] = {
                                "name": holiday.get("name", "")
                            }

        return retval


class Untis(object):
    def __init__(self, credentials):
        self.credentials = credentials

    def get_timetable(self, day):

        monday = day - datetime.timedelta(days=day.weekday())
        friday = monday + datetime.timedelta(days=4)

        untis = webuntis.Session(
            username=self.credentials['username'],
            password=self.credentials['password'],
            server=self.credentials['server'],
            school=self.credentials['school'],
            useragent='WebUntis Test'
        ).login()

        store_holidays = db_utils.get_store_item("untis_holidays", tc.str_to_dict)

        holidays: list[dict] = []

        if store_holidays is None:
            store_holidays = []
            for holiday in untis.holidays():
                store_holidays.append({
                    "start": holiday.start,
                    "end": holiday.end,
                    "name": holiday.name,
                    "short_name": holiday.short_name
                })
            # print(stringify_holidays(holidays))
            db_utils.set_store_item("untis_holidays", stringify_holidays(store_holidays))
            holidays = store_holidays
        else:
            holidays = parse_holidays(store_holidays)

        my_class = untis.klassen().filter(name=self.credentials["class"])[0]

        timetable_week_raw = untis.timetable(klasse=my_class, start=monday, end=friday)

        timetable = []

        TimetableBuilder.clear()

        for period in timetable_week_raw:
            # print(period.start, type(period.start))
            _datetime: datetime.datetime = period.start

            if to_formatted_time(_datetime) not in start_times:
                continue

            room = ""
            try:
                room = str(period.rooms[0])
            except Exception:
                pass

            subject_info = {
                "name": "",
                "fullname": "",
                "code": period.code,
                "room": room
            }
            if len(period.subjects) > 0:
                subject_info["name"] = period.subjects[0].name
                subject_info["fullname"] = period.subjects[0].long_name

                if period.subjects[0].name.lower() not in [s.lower() for s in self.credentials['subjects']]:
                    continue
            else:
                subject_info["name"] = "Irregular"

            TimetableBuilder.add_subject(_datetime, subject_info)
        # for break_ in break_times:
        #     _datetime: datetime.datetime = datetime.datetime.strptime(break_[0], "%H:%M:%S")
        #     TimetableBuilder.add_subject(_datetime, {
        #         "name": "Break",
        #         "fullname": "",
        #         "code": None,
        #         "room": None,
        #     })
        return TimetableBuilder.formatted(monday, holidays=holidays)
