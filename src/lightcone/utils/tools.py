from gramai.utils import nest_dict, is_dict, is_bytes, to_string
from sanic.log import logger
from sanic.request import Request

from lightcone.utils.jsonencoder import dg_json_loads

# 声明一个logging，替代默认的logging
logging = logger


def params_dict_from_request(request: Request, parse_json=False):
    params = {}
    # 参数优先级：request.body > request.form > request.args
    if is_dict(request.args):
        for key in request.args:
            params[key] = request.args.get(key)

    # 更新request.form的参数表
    params.update(nest_dict(request.form))

    if is_bytes(request.body) and 8 < len(request.body):  # 作为JSON格式传递参数，至少需要9位长度{"a":"b"}
        try:
            json_string = to_string(request.body)
            body_dict = dg_json_loads(json_string)
            if is_dict(body_dict):
                for key in body_dict:
                    params[key] = body_dict.get(key)
        except Exception as e:
            logging.warning(f"解析请求body出错：{e}")

    if parse_json:
        try:
            for key in params:
                value = dg_json_loads(params[key])
                params[key] = value
        except Exception as e:
            logging.warning(f"解析参数出错：{e}")
            raise e

    return params


def get_param_from_request(request: Request, key: str, default=None, parse_json=False):
    """
    从sanic request中解析参数
    :param request: sanic reqeust
    :param key: 参数名
    :param default: 默认值
    :param parse_json: 标记是否要解析JSON，默认False
    :return:
    """
    value = default
    # 参数优先级：request.body > request.form > request.args
    if is_dict(request.args) and key in request.args:
        value = request.args.get(key, default)
    request_form = nest_dict(request.form)
    if is_dict(request_form) and key in request_form:
        value = request_form.get(key, default)
    if is_bytes(request.body) and 8 < len(request.body):  # 作为JSON格式传递参数，至少需要9位长度{"a":"b"}
        try:
            body_dict = dg_json_loads(to_string(request.body))
            if is_dict(body_dict) and key in body_dict:
                value = body_dict.get(key, default)
        except Exception as e:
            logging.warning(f"解析请求body出错：{e}")

    if parse_json:
        try:
            value = dg_json_loads(value)
        except Exception as e:
            logging.warning(f"解析参数出错：{e}")
    return value


def request_has_param(request: Request, key: str):
    """
    从sanic request中解析参数
    :param request: sanic reqeust
    :param key: 参数名
    :return:
    """
    params = {}
    # 参数优先级：request.body > request.form > request.args
    if is_dict(request.args) and key in request.args:
        params.update(request.args)
    request_form = nest_dict(request.form)
    if is_dict(request_form) and key in request_form:
        params.update(request_form)
    if is_bytes(request.body):
        try:
            body_dict = dg_json_loads(to_string(request.body))
            if is_dict(body_dict) and key in body_dict:
                params.update(body_dict)
        except Exception as e:
            logging.warning(f"解析请求body出错：{e}")

    value = False
    if key and params:
        value = key in params

    return value
