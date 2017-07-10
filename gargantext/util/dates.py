import os
from gargantext.settings import MEDIA_ROOT

import datetime
import dateutil

def convert_to_date(date):
    if isinstance(date, (int, float)):
        return datetime.datetime.timestamp(date)
    else:
        return dateutil.parser.parse(date)
