import os
from gargantext.settings import MEDIA_ROOT

import datetime
import dateutil

def convert_to_date(date):
    if isinstance(date, (int, float)):
        return datetime.datetime.timestamp(date)
    else:
        return dateutil.parser.parse(date)


def ensure_dir(user):
    '''
    If user is new, folder does not exist yet, create it then
    '''
    dirpath = '%s/corpora/%s' % (MEDIA_ROOT, user.username)
    if not os.path.exists(dirpath):
        print("Creating folder %s" % dirpath)
        os.makedirs(dirpath)
