from sanic import Sanic, Request

from lightcone.core.action import load_action
from lightcone.gate.rest import rest_call_command
from lightcone.gate.stream import stream_call_command

app = Sanic(
    name="Test"
)


# 中间件，设置用户状态到上下文
@app.middleware("request")
async def request_filter(request):
    print(request)


# 中间件，清理上下文
@app.middleware("response")
async def clear_user_context(request, response):
    print(request, response)


@app.route("/action", methods=["GET", "POST"])
async def action_handler(request: Request):
    return load_action(request)


@app.route("/command", methods=["GET", "POST"])
async def command_handler(request: Request):
    return rest_call_command(request)


@app.route("/stream", methods=["GET", "POST"])
async def stream_handler(request):
    return await stream_call_command(request)


if __name__ == "__main__":
    app.run(port=8001)
