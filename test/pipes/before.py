from lightcone.core import Command
from lightcone.gate import CommandResponse
from lightcone.gate.base.pipe import Pipe, PipeReturnStatus


class Before(Pipe):
    def run(self, cmd: Command, response: CommandResponse = None) -> PipeReturnStatus:
        print("Before Pipe")
        return PipeReturnStatus.CONTINUE
