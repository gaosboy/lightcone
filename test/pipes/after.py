from lightcone.core import Command
from lightcone.gate import CommandResponse
from lightcone.gate.base.pipe import Pipe, PipeReturnStatus


class After(Pipe):
    def run(self, cmd: Command, response: CommandResponse = None) -> PipeReturnStatus:
        print("After Pipe")
        return PipeReturnStatus.CONTINUE
