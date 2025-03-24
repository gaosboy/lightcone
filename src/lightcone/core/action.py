from abc import abstractmethod
from enum import Enum
from typing import cast

from gramai.utils.config import Config
from gramai.utils import load_class, concat
from sanic.request import Request
from sanic.response import JSONResponse

from lightcone.utils.jsonencoder import r_json
from lightcone.utils.tools import get_param_from_request
from lightcone.utils.tools import logging

PROJ = Config("proj.ini")


class ActionResponseCode(Enum):
    SUCCESS = 200
    RUNNING_ERROR = 500
    ACTION_NOT_FOUND = 404
    UNEXPECTED_ERROR = -1


# 返回信息模版
MESSAGE_SUCCESS = "Success."
MESSAGE_NOT_FOUND = "Action: {} not found."
MESSAGE_UNEXPECTED = "Got an unexpected error."
MESSAGE_RUNNING_ERROR = "Action running error."


class Action:
    """
    Action的基类，继承自Action的子类命名必须满足**首字母大写，剩余字母全部小写**的规范
    Action的子类文件名必须与类名相同，且全部为小写字母
    子类必须重写render方法，填充渲染逻辑
    返回结果要求必须是字符串、数字或其他符合JSON规范的类型，存入 self.result
    可以把处理结以外的信息通过 self.message 传递
    可以通过 self.request 获取完整请求实例
    """

    def __init__(self, request: Request):
        self._request = request
        self.response_message = None
        self.response_code = ActionResponseCode.UNEXPECTED_ERROR
        self.result = None
        self.run_success = False

    @abstractmethod
    def render(self) -> None:
        pass

    def before_method(self) -> bool:
        """
        在render之前运行

        :return True-可以继续执行Render，False-终止执行，直接构造Response
        """
        _ = self
        return True

    def after_method(self) -> bool:
        """
        在render之后运行

        :return True-正常构造Response，False-忽略忽略self.result，构造出错的Response
        """
        _ = self
        return True

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, value):
        raise AttributeError("只读属性")


def build_response(code: ActionResponseCode, message: str, result=None, success=False) -> JSONResponse:
    return r_json({"code": code.value, "success": success, "message": message, "result": result})


def load_action(request: Request) -> JSONResponse:
    action_name = None
    action_class = None
    try:
        action_name = get_param_from_request(request, "__action")
        class_name = action_name.lower().split(".")[-1].capitalize()
        module_name = concat(PROJ.get("web.action"), action_name.lower(), ".")
        action_class = load_class(module_name, class_name, Action)
    except Exception as e:
        logging.warning(f"加载Action失败：{e}")

    if action_class is None:
        return build_response(code=ActionResponseCode.ACTION_NOT_FOUND,
                              message=MESSAGE_NOT_FOUND)

    current_action = None
    try:
        current_action = cast(Action, action_class(request))
    except Exception as e:
        logging.warning(f"实例化Action失败：{e}")

    if current_action is None:
        return build_response(code=ActionResponseCode.ACTION_NOT_FOUND,
                              message=MESSAGE_NOT_FOUND)

    try:
        # 前置方法运行失败
        if current_action.before_method() is False:
            response_code = current_action.response_code
            if response_code is not None:
                logging.warning(f"Action {action_name} before methods running with an error.")
                return build_response(code=response_code,
                                      message=current_action.response_message)
            else:
                logging.error(f"Action {action_name} before methods running with an unexpected error.")
                return build_response(code=ActionResponseCode.RUNNING_ERROR,
                                      message=current_action.response_message)

        current_action.render()
        response_code = current_action.response_code
        message = current_action.response_message
        result = current_action.result

        # 后置方法运行失败
        if current_action.after_method() is False:
            response_code = current_action.response_code
            if response_code is not None:
                logging.warning(f"Action {action_name} after methods running with an error.")
                return build_response(code=response_code,
                                      message=current_action.response_message)
            else:
                logging.error(f"Action {action_name} after methods running with an unexpected error.")
                return build_response(code=ActionResponseCode.RUNNING_ERROR,
                                      message=current_action.response_message)
    except Exception as e:
        logging.error(f"Action执行异常：{e}")
        return build_response(code=ActionResponseCode.UNEXPECTED_ERROR,
                              message=MESSAGE_UNEXPECTED
                              )

    if response_code.value == ActionResponseCode.SUCCESS.value:
        return build_response(code=ActionResponseCode.SUCCESS,
                              success=True,
                              message=message or MESSAGE_SUCCESS,
                              result=result
                              )
    elif response_code.value == ActionResponseCode.RUNNING_ERROR.value:
        return build_response(code=ActionResponseCode.RUNNING_ERROR,
                              message=message or MESSAGE_RUNNING_ERROR,
                              result=result
                              )
    else:
        logging.warning(f"Action {action_name} running with an unexpected error.")
        return build_response(code=ActionResponseCode.UNEXPECTED_ERROR,
                              message=message or MESSAGE_UNEXPECTED,
                              result=result
                              )
