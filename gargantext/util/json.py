import json
import types
import datetime
import traceback
import inspect


__all__ = ['json_encoder', 'json_dumps']


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        from gargantext.util.db import Base
        if isinstance(obj, Base):
            return {
                key: value
                for key, value in obj.__dict__.items()
                if not key.startswith('_')
            }
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()[:19] + 'Z'
        elif isinstance(obj, Exception):
            tbe = traceback.TracebackException.from_exception(obj)
            return list(line.strip() for line in tbe.format())
        elif hasattr(obj, '__iter__') and not isinstance(obj, dict):
            return list(obj)
        else:
            return super(self.__class__, self).default(obj)

json_encoder = JSONEncoder(indent=4)

def json_dumps(obj):
    return json.dumps(obj, cls=JSONEncoder)
