from typing import Any

from .base.gate import Gate
from .base.response import CommandResponse


class RPC(Gate):
    # 一定要实现这个方法，否则在调用协议检测可能会出错
    @classmethod
    def call(cls, command_id: str, param: Any, method: str) -> CommandResponse:
        return Gate.call(command_id, param, method)
