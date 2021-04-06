import json
import os
import time
from datetime import datetime, timedelta
import decimal

from service.common.exceptions import MissingEnvironmentVariableError


class TimeUtils:
    @staticmethod
    def get_time_iso8601(milliseconds_delta: int = 0) -> str:
        utctime = datetime.utcnow()
        if milliseconds_delta:
            utctime = utctime + timedelta(milliseconds=milliseconds_delta)
        return TimeUtils._utc_time_str_to_iso8601_str(str(utctime))

    @staticmethod
    def _utc_time_str_to_iso8601_str(utc_time_str: str) -> str:
        """
        :param utc_time_str: time in the following format: yyyy-mm-dd hh:mm:ss.f. E.g. '2020-02-28 09:03:54.597915'
        :return:time in ISO 8601 format. E.g. '2020-02-28T09:03:54.597Z'
        """
        return f'{utc_time_str[:10]}T{utc_time_str[11:23]}Z'

    @staticmethod
    def get_current_utc_time_format_for_http_response():
        """
        :return: string representing time adjusted to utc time in the following format: 2020-04-21T06:50:39.331+0000
        """
        utc_time_str = str(datetime.utcnow())
        # not transform this format '2020-04-21T06:50:39.331915' to '2020-04-21T06:50:39.331+0000'
        return f'{utc_time_str[:10]}T{utc_time_str[11:23]}+0000'


def get_env_or_raise(var_name: str) -> str:
    value = os.getenv(var_name, None)
    if value is None:
        raise MissingEnvironmentVariableError(var_name)
    return value


def get_env_vars_with_prefix(prefix):
    return filter(lambda x: x[0].startswith(prefix), os.environ.items())


def json_print(o):
    print(json.dumps(o, indent=4))


def uppercase_to_camelcase(key):
    """
    :param key:
    :type key str
    :return:
    """
    _list = key.lower().split('_')
    _key = _list[0]
    for i in _list[1:]:
        _key += i.capitalize()
    return _key


def is_primitive(obj):
    return type(obj) in [str, int, float, bool]


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        millis_str = '%2.2f ms' % ((te - ts) * 1000)
        if 'logs_accumulator' in kw:
            name = kw.get('log_name', method.__name__)
            kw['logs_accumulator'][name] = millis_str
        else:
            print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed
