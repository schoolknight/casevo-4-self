"""Flovo WebSocket 客户端。

该模块只负责将 Casevo 的工作流请求适配为 Flovo ``WsEnvelope`` 信封，
不在 Python 侧复制或实现 Flovo 的工作流节点逻辑。
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
from collections.abc import Callable
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class FlovoError(Exception):
    """Flovo 客户端异常基类。"""


class FlovoClient:
    """通过 WebSocket 调用 Flovo 工作流。"""

    _DEFAULT_URL = "ws://127.0.0.1:8090"
    _MAX_CONNECT_ATTEMPTS = 3

    def __init__(self, url: str | None = None, timeout: float = 30) -> None:
        """初始化客户端。

        ``url`` 未显式传入时优先读取 ``FLOVO_WS_URL``，否则使用默认地址；
        显式 url 始终优先于环境变量。``timeout`` 是连接及单次收消息超时（秒）。
        """
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        self.url = url if url is not None else os.getenv("FLOVO_WS_URL", self._DEFAULT_URL)
        self.timeout = timeout
        self._active_connections: list[Any] = []

    async def run_workflow(self, workflow_name: str, config: dict, inputs: dict) -> dict:
        """同步执行工作流并收集完整输出。

        一个 output 返回其 ``info``，多个 output 返回按顺序排列的列表，
        没有 output 时返回空字典。
        """
        return await self._execute(workflow_name, config, inputs)

    async def run_workflow_stream(
        self,
        workflow_name: str,
        config: dict,
        inputs: dict,
        callback: Callable[[dict], None],
    ) -> dict:
        """流式执行工作流，并回调 data chunk 与最终 finish 事件。"""
        if not callable(callback):
            raise TypeError("callback must be callable")
        return await self._execute(workflow_name, config, inputs, callback)

    async def close(self) -> None:
        """优雅关闭客户端已建立的 WebSocket 连接。"""
        connections = list(self._active_connections)
        self._active_connections.clear()
        for websocket in connections:
            try:
                result = websocket.close()
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                logger.warning("failed to close Flovo websocket: %s", exc)

    async def _execute(
        self,
        workflow_name: str,
        config: dict,
        inputs: dict,
        callback: Callable[[dict], None] | None = None,
    ) -> dict:
        if not isinstance(workflow_name, str) or not workflow_name:
            raise ValueError("workflow_name must be a non-empty string")
        if not isinstance(config, dict) or not isinstance(inputs, dict):
            raise TypeError("config and inputs must be dictionaries")

        websocket = await self._connect_with_retry(workflow_name)
        self._active_connections.append(websocket)
        try:
            init_message_id = await self._handshake(websocket, workflow_name)
            await self._send_input(websocket, workflow_name, init_message_id + 1, config, inputs)
            outputs: list[Any] = []
            while True:
                envelope = await self._receive_envelope(websocket)
                command = envelope.get("cmd")
                if envelope.get("type") != "service" or envelope.get("workflow") != workflow_name:
                    logger.warning("ignoring unexpected Flovo envelope: %s", envelope)
                    continue
                if command == "output":
                    content = envelope.get("info")
                    outputs.append(content)
                    if callback is not None:
                        await self._invoke_callback(callback, {"status": "data", "content": content})
                elif command == "workflow_finished":
                    result = self._summarize_outputs(outputs)
                    if callback is not None:
                        await self._invoke_callback(callback, {"status": "finish", "content": result})
                    return result
                else:
                    logger.warning("ignoring unknown Flovo command: %s", command)
        except asyncio.TimeoutError as exc:
            raise FlovoError("timed out waiting for Flovo response") from exc
        except ConnectionClosed as exc:
            raise FlovoError("Flovo server closed the WebSocket connection") from exc
        except FlovoError:
            raise
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise FlovoError(f"invalid Flovo protocol message: {exc}") from exc
        finally:
            if websocket in self._active_connections:
                self._active_connections.remove(websocket)
            try:
                result = websocket.close()
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                logger.warning("failed to close Flovo websocket: %s", exc)

    async def _connect_with_retry(self, workflow_name: str) -> Any:
        endpoint = self._workflow_url(workflow_name)
        last_error: Exception | None = None
        for attempt in range(self._MAX_CONNECT_ATTEMPTS):
            try:
                # wait_for 兼容 websockets 16 与仅接受 url 参数的 fake websocket。
                return await asyncio.wait_for(websockets.connect(endpoint), self.timeout)
            except asyncio.TimeoutError as exc:
                last_error = exc
            except Exception as exc:
                last_error = exc
            if attempt < self._MAX_CONNECT_ATTEMPTS - 1:
                delay = 2**attempt
                logger.warning(
                    "Flovo connection attempt %d/%d failed; retrying in %ss",
                    attempt + 1,
                    self._MAX_CONNECT_ATTEMPTS,
                    delay,
                )
                await asyncio.sleep(delay)
        raise FlovoError(f"failed to connect to Flovo after {self._MAX_CONNECT_ATTEMPTS} attempts") from last_error

    async def _handshake(self, websocket: Any, workflow_name: str) -> int:
        connect_ok = await self._receive_until(websocket, workflow_name, "connect_ok")
        if connect_ok.get("message_id") not in (0, None):
            logger.warning("unexpected connect_ok message_id: %s", connect_ok.get("message_id"))

        init_message_id = 1
        await self._send_envelope(websocket, workflow_name, "init_report", init_message_id, {})
        while True:
            response = await self._receive_envelope(websocket)
            if response.get("type") != "service" or response.get("workflow") != workflow_name:
                logger.warning("ignoring unexpected handshake envelope: %s", response)
                continue
            if response.get("cmd") != "init_ok":
                logger.warning("ignoring unexpected handshake command: %s", response.get("cmd"))
                continue
            if response.get("message_id") != init_message_id:
                logger.warning(
                    "ignoring init_ok with mismatched message_id: expected %s, got %s",
                    init_message_id,
                    response.get("message_id"),
                )
                continue
            return init_message_id

    async def _send_input(
        self,
        websocket: Any,
        workflow_name: str,
        message_id: int,
        config: dict,
        inputs: dict,
    ) -> None:
        # Flovo 将工作流输入直接放在 info 中；非空 config 与 inputs 合并，
        # inputs 优先覆盖同名配置，避免额外嵌套破坏服务端字段读取。
        info = dict(inputs) if not config else {**config, **inputs}
        await self._send_envelope(websocket, workflow_name, "send_input", message_id, info)

    async def _send_envelope(
        self, websocket: Any, workflow_name: str, command: str, message_id: int, info: dict
    ) -> None:
        envelope = {
            "type": "service",
            "workflow": workflow_name,
            "cmd": command,
            "message_id": message_id,
            "info": info,
            "resource": None,
        }
        result = websocket.send(json.dumps(envelope, ensure_ascii=False))
        if inspect.isawaitable(result):
            await result

    async def _receive_until(self, websocket: Any, workflow_name: str, command: str) -> dict:
        while True:
            envelope = await self._receive_envelope(websocket)
            if (
                envelope.get("type") == "service"
                and envelope.get("workflow") == workflow_name
                and envelope.get("cmd") == command
            ):
                return envelope
            logger.warning("ignoring unexpected Flovo envelope while waiting for %s: %s", command, envelope)

    async def _receive_envelope(self, websocket: Any) -> dict:
        while True:
            message = await asyncio.wait_for(websocket.recv(), self.timeout)
            if not isinstance(message, str):
                # Ping/Pong/二进制消息由 websockets 层处理或直接跳过。
                continue
            envelope = json.loads(message)
            if not isinstance(envelope, dict):
                raise FlovoError("Flovo message must be a JSON object")
            return envelope

    @staticmethod
    async def _invoke_callback(callback: Callable[[dict], None], payload: dict) -> None:
        result = callback(payload)
        if inspect.isawaitable(result):
            await result

    @staticmethod
    def _summarize_outputs(outputs: list[Any]) -> Any:
        if not outputs:
            return {}
        return outputs[0] if len(outputs) == 1 else outputs

    def _workflow_url(self, workflow_name: str) -> str:
        parsed = urlsplit(self.url)
        base_path = parsed.path.rstrip("/")
        path = f"{base_path}/{quote(workflow_name, safe='')}"
        return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))
