from abc import ABC
from enum import Enum

from gramai.utils import is_dict, is_str
from sanic import Request

from lightcone.gate.base.gate import Gate
from lightcone.utils import logging
from lightcone.utils import params_dict_from_request

STREAM_PARAM_KEY_COMMAND_ID = "command_id"
STREAM_PARAM_KEY_METHOD = "method"


class StreamContext:
    def __init__(self, request):
        self._response = None
        self.request = request

    async def rebuild_response(self, status: int = None, headers=None):
        """
        供异步指令回调，重设response status 和 header
        返回指令执行状态
        """
        try:
            response = await self._build_response()
            if status is not None:
                response.status = int(status)
            if is_dict(headers):
                for key in headers:
                    value = headers.get(key)
                    if is_str(key) and is_str(value):
                        response.headers[key] = headers[key]
        except Exception as e:
            logging.warning(f"重建event-stream response头异常：{e}")

    async def send_event_message(self, message):
        try:
            response = await self._build_response()
            event_message = f"data: {message}\n\n"
            await response.send(event_message)
        except Exception as e:
            logging.warning(f"steam response发送消息异常：{e}")

    async def eof(self):
        try:
            response = await self._build_response()
            await response.eof()
        except Exception as e:
            logging.warning(f"steam response eof异常：{e}")

    async def _build_response(self):
        if self._response is None and self.request is not None:
            self._response = await self.request.respond(content_type="text/event-stream;charset=UTF-8")
        return self._response


async def stream_call_command(request: Request):
    try:
        stream_context = StreamContext(request)
        await STREAM.call_from_request(request=request,
                                       callback=stream_context.send_event_message,
                                       header_call=stream_context.rebuild_response
                                       )
        await stream_context.eof()
    except Exception as e:
        logging.error(f"Error during calling streaming command : {e}")


class ParamType(Enum):
    STR = "str"
    JSON = "json"
    FILE = "file"


class STREAM(Gate, ABC):
    @classmethod
    async def call_from_request(cls, request: Request, callback, header_call):
        param = params_dict_from_request(request)
        command_id = param.pop(STREAM_PARAM_KEY_COMMAND_ID)
        method = param.pop(STREAM_PARAM_KEY_METHOD)

        await cls.async_call(command_id, param, method, callback, header_call)
