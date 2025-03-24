from typing import cast, Any

from gramai.utils import load_class, concat
from gramai.utils.config import Config

from lightcone.core import Command
from lightcone.gate import build_no_command_response, build_fail_response, build_bad_request_response
from lightcone.gate import build_success_response, CommandResponse, build_error_response
from lightcone.gate.base.pipe import Pipe, PipeReturnStatus
from lightcone.utils.tools import logging

PROJ = Config("proj.ini")
pipe_module_prefix = PROJ.get("web.pipe")
pipe_config = Config("pipes.json")
command_config = Config("commands.json")


class Gate:

    @staticmethod
    def __before_method(cmd: Command):
        response = None
        try:
            before_pipes = pipe_config.get(key=f"{cmd.command_id}.before",
                                           default=pipe_config.get("default.before", []))
            current_pipe = None
            for pipe in before_pipes:
                module_name = concat(pipe_module_prefix, pipe.lower(), ".")
                class_name = pipe
                pipe_class = load_class(module_name, class_name, Pipe)
                if pipe_class is None:
                    continue

                # 创建类的实例（假设类没有初始化参数，或你需要添加参数）
                current_pipe = cast(Pipe, pipe_class())
                pipe_status = current_pipe.run(cmd)
                if isinstance(pipe_status, PipeReturnStatus):
                    if pipe_status == PipeReturnStatus.INTERRUPT:
                        break
                    else:
                        # 如果没有被中断，不记录current pipe
                        current_pipe = None
                else:
                    logging.error(f"pipe{module_name}.{class_name}执行返回不存在的状态码")
                    break
            if current_pipe is not None:
                if current_pipe.response is not None:
                    return current_pipe.response
                else:
                    return build_bad_request_response(cmd)
        except Exception as e:
            logging.error(f"前置方法执行异常：{e}")
            return build_bad_request_response(cmd)
        return response

    @staticmethod
    def __after_method(cmd: Command, response: CommandResponse):
        try:
            after_pipes = pipe_config.get(key=f"{cmd.command_id}.after",
                                          default=pipe_config.get("default.after", []))
            current_pipe = None
            for pipe in after_pipes:
                module_name = concat(pipe_module_prefix, pipe.lower(), ".")
                class_name = pipe.split(".")[-1]
                pipe_class = load_class(module_name, class_name, Pipe)
                if pipe_class is None:
                    continue

                # 创建类的实例（假设类没有初始化参数，或你需要添加参数）
                current_pipe = cast(Pipe, pipe_class())
                pipe_status = current_pipe.run(cmd)
                if isinstance(pipe_status, PipeReturnStatus):
                    if pipe_status == PipeReturnStatus.INTERRUPT.value:
                        break
                    else:
                        # 如果没有被中断，不记录current pipe
                        current_pipe = None
                else:
                    logging.error(f"pipe{module_name}.{class_name}执行返回不存在的状态码")
                    break
            if current_pipe is not None:
                if current_pipe.response is not None:
                    return current_pipe.response
                else:
                    return build_bad_request_response(cmd)
        except Exception as e:
            logging.error(f"后置方法执行异常：{e}")
            return build_bad_request_response(cmd)
        return response

    @classmethod
    def call(cls, command_id: str, param: Any, method: str) -> CommandResponse:
        cmd = cls._build_command(command_id, method)
        if cmd is None:
            return build_no_command_response(command_id)
        else:
            return Gate._eval(cmd, param, method)

    @classmethod
    def _eval(cls, cmd: Command, param, method):
        before_response = cls.__before_method(cmd)
        if before_response is not None:
            return before_response

        try:
            # 调用run方法，执行指令
            if cmd.run(param, method):
                response = build_success_response(cmd)
            else:
                return build_fail_response(cmd)
        except Exception as e:
            logging.error(f"：{e}")
            return build_error_response(cmd)

        after_response = cls.__before_method(cmd)
        if after_response is not None:
            return after_response

        return response or build_error_response(cmd)

    @classmethod
    async def async_call(cls, command_id: str, param: Any, method: str, callback=None, header_call=None):
        cmd = cls._build_command(command_id, method, callback, header_call)
        if cmd is None:
            return build_no_command_response(command_id)
        else:
            return await cls._async_eval(cmd, param, method)

    @classmethod
    async def _async_eval(cls, cmd: Command, param, method):
        before_response = cls.__before_method(cmd)
        if before_response is not None:
            return before_response

        response = None
        try:
            # 调用run方法，执行指令
            if await cmd.async_run(param, method):
                response = build_success_response(cmd)
        except Exception as e:
            logging.error(f"指令执行异常：{e}")
            return build_error_response(cmd)

        after_response = cls.__before_method(cmd)
        if after_response is not None:
            return after_response

        return response or build_error_response(cmd)

    @classmethod
    def _build_command(cls, command_id: str, method: str, callback=None, header_call=None):
        command_class = None
        try:
            if command_id is None or not isinstance(command_id, str):
                return None

            # 没有配置
            if command_config is None:
                return None

            # 获取指令信息，类名和模块名
            class_name = command_config.get(f"{command_id}.class", "")
            module_name = command_config.get(f"{command_id}.module")
            command_class = load_class(module_name, class_name)
        except Exception as e:
            logging.warning(f"加载指令出错：{e}")

        if command_class is None:
            return None

        cmd = None
        try:
            # 创建类的实例
            cmd = command_class(command_id, method)
        except Exception as e:
            logging.error(f"指令执行异常：{e}")

        # 实例化失败
        if not isinstance(cmd, Command):
            return None

        cmd = cast(Command, cmd)
        cmd.protocol = cls.__name__
        cmd.stream_callback = callback if callable(callback) else None
        cmd.header_callback = header_call if callable(header_call) else None
        return cmd
