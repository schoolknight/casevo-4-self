"""通过 WebSocket 实时转发 :class:`TotLogStream` 日志事件。"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed

from casevo.util.tot_log_stream import TotLogStream


logger = logging.getLogger(__name__)


class LogStreamServer:
    """在后台线程中运行的轻量日志流 WebSocket 服务。"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        """配置监听地址；构造实例不会创建线程或事件循环。

        参数:
        - host: WebSocket 服务监听地址。
        - port: WebSocket 服务监听端口；传入 ``0`` 时由系统分配空闲端口。
        """
        self.host = host
        self.port = port
        self._lifecycle_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server: Any | None = None
        self._clients: set[Any] = set()
        self._subscription_ids: set[int] = set()
        self._ready = threading.Event()
        self._startup_error: BaseException | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """返回服务是否已完成监听且尚未停止。"""
        with self._state_lock:
            return self._running

    def start(self) -> None:
        """在守护线程中启动服务；服务已运行时直接返回。

        启动会等待后台服务完成端口绑定，以便方法返回后客户端可立即连接。
        绑定失败时抛出 ``RuntimeError``，并保留原始异常作为 cause。
        """
        with self._lifecycle_lock:
            if self._thread is not None and self._thread.is_alive():
                return

            self._ready = threading.Event()
            self._startup_error = None
            thread = threading.Thread(
                target=self._run,
                name="casevo-log-stream-server",
                daemon=True,
            )
            self._thread = thread
            thread.start()

            if not self._ready.wait(timeout=10):
                raise RuntimeError("LogStreamServer did not start within 10 seconds")

            if self._startup_error is not None:
                thread.join(timeout=10)
                self._thread = None
                raise RuntimeError("LogStreamServer failed to start") from self._startup_error

    def stop(self) -> None:
        """关闭监听器和客户端、清理订阅并结束后台线程。

        服务未运行时直接返回；停止后的同一实例可以再次调用 ``start``。
        """
        with self._lifecycle_lock:
            thread = self._thread
            with self._state_lock:
                loop = self._loop
            if thread is None or not thread.is_alive() or loop is None:
                self._thread = None
                return

            future = asyncio.run_coroutine_threadsafe(self._shutdown(), loop)
            try:
                future.result(timeout=10)
            except Exception:
                logger.exception("failed to stop LogStreamServer cleanly")
            thread.join(timeout=10)
            if thread.is_alive():
                logger.error("LogStreamServer thread did not stop within 10 seconds")
            else:
                self._thread = None

    def _run(self) -> None:
        """创建并独占后台事件循环，直到服务关闭。"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with self._state_lock:
            self._loop = loop

        try:
            loop.run_until_complete(self._serve())
        except BaseException as exc:
            self._startup_error = exc
            self._ready.set()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            with self._state_lock:
                self._running = False
                self._loop = None
                self._server = None

    async def _serve(self) -> None:
        """绑定端口并等待 WebSocket 服务关闭。"""
        async with websockets.serve(self._handle_connection, self.host, self.port) as server:
            self._server = server
            if server.sockets:
                self.port = server.sockets[0].getsockname()[1]
            with self._state_lock:
                self._running = True
            self._ready.set()
            await server.wait_closed()

    async def _handle_connection(self, websocket: Any) -> None:
        """为一个客户端建立独立队列、订阅和发送任务。"""
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        def enqueue(event: dict[str, Any]) -> None:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, event)
            except RuntimeError:
                # 事件循环关闭与同步派发并发时丢弃该连接的尾部事件。
                logger.debug("discarded log event while client loop was closing")

        subscription_id = TotLogStream.subscribe(enqueue)
        self._subscription_ids.add(subscription_id)
        self._clients.add(websocket)
        sender = asyncio.create_task(self._send_events(websocket, queue))
        closed = asyncio.create_task(websocket.wait_closed())

        try:
            done, _ = await asyncio.wait(
                {sender, closed}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                await task
        except (ConnectionClosed, asyncio.CancelledError):
            pass
        except Exception:
            logger.exception("LogStreamServer client handler failed")
        finally:
            sender.cancel()
            closed.cancel()
            await asyncio.gather(sender, closed, return_exceptions=True)
            self._clients.discard(websocket)
            TotLogStream.unsubscribe(subscription_id)
            self._subscription_ids.discard(subscription_id)

    async def _send_events(
        self, websocket: Any, queue: asyncio.Queue[dict[str, Any]]
    ) -> None:
        """从单客户端队列取出事件并按固定消息格式发送。"""
        while True:
            event = await queue.get()
            message = {"status": "data", "event": event}
            await websocket.send(json.dumps(message, ensure_ascii=False))

    async def _shutdown(self) -> None:
        """在服务事件循环内关闭连接，并确保所有订阅均被清理。"""
        with self._state_lock:
            self._running = False

        server = self._server
        if server is not None:
            server.close()

        clients = tuple(self._clients)
        if clients:
            await asyncio.gather(
                *(client.close(code=1001, reason="server stopping") for client in clients),
                return_exceptions=True,
            )
        if server is not None:
            await server.wait_closed()

        # 正常情况下连接 handler 已完成退订；此处防御性清理启动/关闭竞态。
        for subscription_id in tuple(self._subscription_ids):
            TotLogStream.unsubscribe(subscription_id)
            self._subscription_ids.discard(subscription_id)
