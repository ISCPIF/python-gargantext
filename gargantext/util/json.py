import json
import datetime
import traceback


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()[:19] + 'Z'
        elif isinstance(obj, (set, tuple)):
            return list(obj)
        elif isinstance(obj, Exception):
            tbe = traceback.TracebackException.from_exception(obj)
            return list(line.strip() for line in tbe.format())
        else:
            return super(self.__class__, self).default(obj)

json_encoder = JSONEncoder(indent=4)

def json_dumps(obj):
    return json.dumps(obj, cls=JSONEncoder)
