from datetime import datetime, timezone, timedelta, UTC
from base64 import b64decode
import json

# fmt: off
def utc_plus_8() -> datetime:
    return datetime.now(UTC).astimezone(timezone(timedelta(hours=8)))
# fmt: on


def timestamp_13_digit() -> int:
    return int(datetime.timestamp(utc_plus_8()) * 1000)


def get_today_date_str():
    return datetime.strftime(utc_plus_8(), "%Y-%m-%d")


def decode_str_with_base64(string: str) -> str:
    return b64decode(string.encode("utf-8")).decode("utf-8")


def decode_to_json(string: str):
    return json.loads(decode_str_with_base64(string))


def find_available_classroom(data, floor: str, periods: list[int]):
    """
    `data`: Classroom data\n
    `floor`: target floor\n
    `periods`: target periods, scale from 1~10, such as [1,2,5,6]
    """
    available_classrooms = []
    for classroom in data:
        if int(classroom["floor"]) == int(floor):
            # Check if target period is available, 0 for available, 1 for occupied.
            occupy_units = classroom["occupy_units"]
            is_available = True
            for period in periods:
                if occupy_units[period - 1] == "1":
                    is_available = False
                    break
            if is_available:
                available_classrooms.append(classroom["room_name"])

    return available_classrooms
