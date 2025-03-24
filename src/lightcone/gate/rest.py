from abc import ABC
from enum import Enum

from sanic.request import Request

from lightcone.utils.tools import logging, params_dict_from_request
from lightcone.utils.jsonencoder import r_json
from .base.gate import Gate
from .base.response import CommandResponse, CommandResponseCode

# 请求中的参数名
REST_PARAM_KEY_COMMAND_ID = "__command_id"
REST_PARAM_KEY_METHOD = "__method"


def rest_call_command(request: Request):
    return REST.call_from_reqeust(request)


class ParamType(Enum):
    STR = "str"
    JSON = "json"
    FILE = "file"


class REST(Gate, ABC):
    @classmethod
    def call_from_reqeust(cls, request: Request):
        """
        从request中读取参数，执行指令
        :param request: 从GET或POST中读取command_id和params两个字段，POST优先级更高
                        自动识别params是否可被JSON反序列化，并反序列化为字典
        :return:
        """
        try:
            param = params_dict_from_request(request)
        except Exception as e:
            logging.error(f"解析参数列表出错：{e}")
            return r_json(
                {"code": CommandResponseCode.BAD_REQUEST.value,
                 "message": "参数异常",
                 "result": "",
                 "command_id": "",
                 "method": "",
                 "success": False
                 })

        command_id = param.pop(REST_PARAM_KEY_COMMAND_ID)
        method = param.pop(REST_PARAM_KEY_METHOD)

        response = cls.call(command_id, param, method)
        if response and isinstance(response, CommandResponse):
            try:
                response_json = response.to_dict()
                if CommandResponseCode.SUCCESS.value == response.code.value:
                    response_json["success"] = True
                else:
                    response_json["success"] = False
                ret = r_json(body=response_json)
            except Exception as e:
                logging.error(f"序列化失败: {e}")
                ret = r_json(
                    {"code": CommandResponseCode.ERROR.value,
                     "message": "序列化失败",
                     "result": "",
                     "command_id": command_id,
                     "method": method,
                     "success": False
                     })
        else:
            ret = r_json(
                {"code": CommandResponseCode.ERROR.value,
                 "message": "指令执行错误",
                 "result": "",
                 "command_id": command_id,
                 "method": method,
                 "success": False
                 })
        return ret
