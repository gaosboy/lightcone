from abc import ABC

from lightcone.core import Command


class Bar(Command, ABC):
    def run(self, param, method) -> bool:
        self.result = f"Command Bar result\nparam:{param}\nmethod:{method}"
        return True

    def async_run(self, param, method) -> bool:
        return False