from enum import Enum

from lightcone.core import Command


class CommandResponseCode(Enum):
    SUCCESS = 200
    FAIL = 503
    ERROR = 500
    BAD_REQUEST = 400
    NOT_LOGIN = 401
    NO_RIGHT = 403
    NO_COMMAND = 404


# 返回信息模版
MESSAGE_NOT_LOGIN = "尚未登录，请登录后重试"
MESSAGE_NO_RIGHT = "您无权执行这个操作"
MESSAGE_SUCCESS = "执行成功"
MESSAGE_ERROR = "操作执行失败"
MESSAGE_NO_COMMAND = "找不到您要执行的操作"
MESSAGE_BAD_PROTOCOL = "无法执行这个操作"


def build_not_login_response(cmd: Command):
    response = CommandResponse(code=CommandResponseCode.NOT_LOGIN,
                               message=MESSAGE_NOT_LOGIN.format(cmd.command_id),
                               command=cmd)
    return response


def build_no_right_response(cmd: Command):
    response = CommandResponse(code=CommandResponseCode.NO_RIGHT,
                               message=MESSAGE_NO_RIGHT.format(cmd.command_id),
                               command=cmd)
    return response


def build_success_response(cmd: Command):
    response = CommandResponse(code=CommandResponseCode.SUCCESS,
                               message=MESSAGE_SUCCESS.format(cmd.command_id),
                               command=cmd)
    return response


def build_error_response(cmd: Command):
    response = CommandResponse(code=CommandResponseCode.ERROR,
                               message=MESSAGE_ERROR.format(cmd.command_id),
                               command=cmd)
    return response


def build_fail_response(cmd: Command):
    response = CommandResponse(code=CommandResponseCode.FAIL,
                               message=MESSAGE_ERROR.format(cmd.command_id),
                               command=cmd)
    return response


def build_bad_request_response(cmd: Command):
    response = CommandResponse(code=CommandResponseCode.BAD_REQUEST,
                               message=MESSAGE_ERROR.format(cmd.command_id),
                               command=cmd)
    return response


def build_protocol_not_support_response(command_id):
    response = CommandResponse(code=CommandResponseCode.NO_COMMAND,
                               message=MESSAGE_BAD_PROTOCOL.format(command_id))
    response.command_id = command_id
    return response


def build_no_command_response(command_id):
    response = CommandResponse(code=CommandResponseCode.NO_COMMAND,
                               message=MESSAGE_NO_COMMAND.format(command_id))
    response.command_id = command_id
    return response


class CommandResponse:
    def __init__(self, code, message=None, command=None):
        self._code = code
        self._result = None
        self._message = message
        self._command = command
        if command and isinstance(command, Command):
            self._command_id = command.command_id
            self._method = command.method
            self._result = command.result
        else:
            self._command_id = None
            self._method = None
            self._result = None

    def to_dict(self):
        return {"code": self.code.value,
                "message": self.message,
                "result": self.result,
                "command_id": self.command_id,
                "method": self.method
                }

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        """
        只读
        :return:
        """
        raise AttributeError("只读属性")

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        """
        只读
        :param value:
        :return:
        """
        raise AttributeError("只读属性")

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        """
        只读
        :param value:
        :return:
        """
        raise AttributeError("只读属性")

    @property
    def command(self):
        return self._command

    @command.setter
    def command(self, value):
        raise AttributeError("只读属性")

    @property
    def command_id(self):
        return self._command_id

    @command_id.setter
    def command_id(self, value):
        self._command_id = value

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, value):
        raise AttributeError("只读属性")
