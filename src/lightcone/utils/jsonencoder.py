import json
import uuid
from datetime import datetime

from sanic.response import json as sanic_json


def dg_json_dumps(data, ensure_ascii=False):
    """
    序列化为字符串
    """
    def encode(obj):
        if isinstance(obj, datetime):
            return int(obj.timestamp())
        elif isinstance(obj, uuid.UUID):
            return obj.hex
        elif isinstance(obj, int):
            return int(obj)
        elif isinstance(obj, float):
            return float(obj)
        elif obj is None:
            return ""
        raise TypeError(f"Type {type(obj)} not serializable")

    return json.dumps(data, default=encode, ensure_ascii=ensure_ascii)


def dg_json_loads(string):
    """
    反序列化为对象
    """
    return json.loads(string)


class DGJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return int(o.timestamp())
        elif isinstance(o, uuid.UUID):
            return o.hex
        elif o is None:
            return ""
        return super().default(o)


def r_json(body):
    return sanic_json(body=body, dumps=dg_json_dumps)
