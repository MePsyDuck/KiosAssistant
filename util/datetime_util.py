from datetime import datetime

import dateparser
import parsedatetime
import pytz
from dateparser.search import search_dates
from dateutil.relativedelta import relativedelta

cal = parsedatetime.Calendar()


def parse_time(time_string, base_time, user):
    timezone = user.time_zone if user else None
    base_time = datetime_as_timezone(base_time, timezone)

    try:
        date_time = dateparser.parse(
            time_string,
            languages=['en'],
            settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
    except Exception:
        date_time = None

    if date_time is None:
        try:
            results = search_dates(
                time_string,
                languages=['en'],
                settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
            if results is not None:
                temp_time = results[0][1]
                if temp_time.tzinfo is None:
                    temp_time = datetime_force_utc(temp_time)

                if temp_time > base_time:
                    date_time = results[0][1]
            else:
                date_time = None
        except Exception:
            date_time = None

    if date_time is None:
        try:
            date_time, result_code = cal.parseDT(time_string, base_time)
            if result_code == 0:
                date_time = None
        except Exception:
            date_time = None

    if date_time is None:
        return None

    if date_time.tzinfo is None:
        if timezone is not None:
            date_time = pytz.timezone(timezone).localize(date_time)
        else:
            date_time = datetime_force_utc(date_time)

    date_time = datetime_as_utc(date_time)

    return date_time


def render_time(date_time, user=None, add_link=False):
    timezone = user.time_zone if user else None
    time_format = user.time_format if user else None
    if time_format == "12":
        format_string = "%Y-%m-%d %I:%M:%S %p %Z"
    else:
        format_string = "%Y-%m-%d %H:%M:%S %Z"

    return f'{datetime_as_timezone(date_time, timezone).strftime(format_string)}' + \
           (f'(http://www.wolframalpha.com/input/?i={date_time.strftime("%Y-%m-%d %H:%M:%S %Z")} To Local Time)'.replace(
               ' ', '%20') if add_link else ' ')


def render_time_diff(start_date, end_date, show_seconds=False):
    seconds = int((end_date - start_date).total_seconds())
    if seconds > 59:
        try:
            adjusted_end_date = start_date + relativedelta(seconds=int(min(seconds * 1.02, seconds + 60 * 60 * 24)))
        except OverflowError:
            adjusted_end_date = datetime_force_utc(datetime(year=9999, month=12, day=31))

        delta = relativedelta(adjusted_end_date, start_date)
    else:
        delta = relativedelta(end_date, start_date)

    if delta.years > 0:
        return f"{delta.years} year{('s' if delta.years > 1 else '')}"
    elif delta.months > 0:
        return f"{delta.months} month{('s' if delta.months > 1 else '')}"
    elif delta.days > 0:
        return f"{delta.days} day{('s' if delta.days > 1 else '')}"
    elif delta.hours > 0:
        return f"{delta.hours} hour{('s' if delta.hours > 1 else '')}"
    elif delta.minutes > 0:
        return f"{delta.minutes} minute{('s' if delta.minutes > 1 else '')}"
    elif show_seconds and delta.seconds > 0:
        return f"{delta.seconds} second{('s' if delta.seconds > 1 else '')}"
    else:
        return ""


def datetime_as_timezone(date_time, timezone):
    if timezone:
        return date_time.astimezone(pytz.timezone(timezone))
    else:
        return date_time


def datetime_as_utc(date_time):
    return date_time.astimezone(pytz.utc)


def datetime_force_utc(date_time):
    return pytz.utc.localize(date_time)


def utc_now():
    return datetime.now(pytz.utc)


def valid_timezone(timezone):
    return timezone in pytz.all_timezones


def valid_time_format(time_format):
    return time_format in ['12', '24']


def datetime_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp)


def timestamp_from_datetime(date_time):
    return datetime.timestamp(date_time)
