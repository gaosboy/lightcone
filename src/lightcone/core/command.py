from abc import abstractmethod, ABC
from typing import final


class Command(ABC):
    """
    指令的基类
    """

    def __init__(self, command_id, method):
        self._command_id = command_id or ""
        self._method = method
        self.result = None
        self.protocol = None
        self.stream_callback = None
        self.header_callback = None

    @abstractmethod
    def run(self, param, method) -> bool:
        """
        执行指令，需要被重写。
        指令运行结果要存入 self.result
        :return: True-成功 False-失败
        """

    @abstractmethod
    async def async_run(self, param, method) -> bool:
        """
            异步执行指令，需要被重写。
        """
    @property
    @final
    def command_id(self):
        return self._command_id

    @command_id.setter
    @final
    def command_id(self, value):
        raise AttributeError("只读属性")

    @property
    @final
    def method(self):
        return self._method

    @method.setter
    @final
    def method(self, value):
        raise AttributeError("只读属性")
