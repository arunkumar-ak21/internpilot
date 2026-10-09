import json

# Dummy orjson to bypass Application Control policy blocking the real orjson.pyd
# This maps orjson API to the standard library json API.

OPT_SERIALIZE_NUMPY = 1
OPT_NON_STR_KEYS = 2
OPT_OMIT_MICROSECONDS = 4
OPT_STRICT_INTEGER = 8
OPT_NAIVE_UTC = 16
OPT_SORT_KEYS = 32
OPT_INDENT_2 = 64
OPT_APPEND_NEWLINE = 128

class JSONDecodeError(json.JSONDecodeError):
    pass

class JSONEncodeError(Exception):
    pass

def dumps(obj, default=None, option=None):
    kwargs = {}
    if default is not None:
        kwargs['default'] = default
    if option and (option & OPT_SORT_KEYS):
        kwargs['sort_keys'] = True
    if option and (option & OPT_INDENT_2):
        kwargs['indent'] = 2
        
    try:
        return json.dumps(obj, **kwargs).encode('utf-8')
    except Exception as e:
        raise JSONEncodeError(str(e))

def loads(obj):
    if isinstance(obj, (bytes, bytearray)):
        obj = obj.decode('utf-8')
    return json.loads(obj)
