from abc import abstractmethod, ABC
from enum import Enum

from lightcone.core import Command
from lightcone.gate import CommandResponse


class PipeReturnStatus(Enum):
    """
    Pipe执行后的返回状态
    """
    INTERRUPT = -1  # 中断执行
    CONTINUE = 0  # 继续执行（失败）
    PASS = 1  # 继续执行（成功）


class Pipe(ABC):
    """
    Pipe的基类
    Pipe的子类文件名必须与类名相同，且全部为小写字母
    子类必须重写run方法，填充逻辑
    若需要传低Pipe运行的返回结果，需要构造 gate.vo.Response 实例，并存入 self.response
    当run返回的code为 PipeReturnStatus.INTERRUPT 时，则指令执行器将以该Pipe构造的response作为指令执行返回值
    可以把处理结果以外的信息通过 self.message 传递
    """
    def __init__(self):
        # 运行后的信息
        self._message = None
        self._response = None

    @abstractmethod
    def run(self, cmd: Command, response: CommandResponse = None) -> PipeReturnStatus:
        """
        执行指令，需要被重写
        :return:
        """

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, value):
        self._message = value

    @property
    def response(self) -> CommandResponse:
        return self._response

    @response.setter
    def response(self, value):
        self._response = value
