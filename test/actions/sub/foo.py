from lightcone.core import Action, ActionResponseCode


class Foo(Action):
    def render(self) -> None:
        self.run_success = True
        self.response_code = ActionResponseCode.SUCCESS
        self.result = "Foo action result"
        self.response_message = "Foo action message"
