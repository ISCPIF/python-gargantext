import os
from gargantext.settings import MEDIA_ROOT

from datetime import MINYEAR
from dateutil.parser import parse as parse_datetime_flexible
from django.utils.dateparse import parse_datetime
from django.utils.timezone import datetime as _datetime, utc as UTC, now as utcnow

__all__ = ['convert_to_datetime', 'datetime', 'MINYEAR']


class datetime(_datetime):
    @staticmethod
    def now():
        return utcnow()

    @staticmethod
    def utcfromtimestamp(ts):
        return _datetime.utcfromtimestamp(ts).replace(tzinfo=UTC)

    @staticmethod
    def parse(s):
        dt = parse_datetime(s) or \
             parse_datetime_flexible(s, default=datetime(MINYEAR, 1, 1))
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)


def convert_to_datetime(dt):
    if isinstance(dt, (int, float)):
        return datetime.utcfromtimestamp(dt)

    elif isinstance(dt, str):
        return datetime.parse(dt)

    elif isinstance(dt, _datetime):
        args = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        return datetime(*args, tzinfo=dt.tzinfo or UTC).astimezone(UTC)

    else:
        raise ValueError("Can't convert to datetime: %r" % dt)
