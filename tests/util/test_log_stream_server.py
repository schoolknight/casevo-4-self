"""LogStreamServer 本机 WebSocket 集成测试。"""

from __future__ import annotations

import asyncio
import json

import pytest
import websockets
from websockets.exceptions import ConnectionClosed

from casevo.util.log_stream_server import LogStreamServer
from casevo.util.tot_log_stream import TotLogStream


pytestmark = pytest.mark.integration


def _clear_subscribers() -> None:
    """通过公开退订 API 清理测试进程内的类级订阅状态。"""
    with TotLogStream._subscribers_lock:
        subscription_ids = [item["sub_id"] for item in TotLogStream._subscribers]
    for subscription_id in subscription_ids:
        TotLogStream.unsubscribe(subscription_id)


def _subscriber_count() -> int:
    """读取订阅数量，用于验证异步连接清理已完成。"""
    with TotLogStream._subscribers_lock:
        return len(TotLogStream._subscribers)


async def _wait_for_subscribers(expected: int) -> None:
    """等待服务连接处理器完成订阅或退订。"""
    for _ in range(100):
        if _subscriber_count() == expected:
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"expected {expected} subscribers, got {_subscriber_count()}")


@pytest.fixture(autouse=True)
def initialized_log(tmp_path):
    """隔离日志文件和 TotLogStream 类级订阅状态。"""
    _clear_subscribers()
    TotLogStream.init_log(2, str(tmp_path), buffer_size=10_000, clear_old=True)
    yield tmp_path
    _clear_subscribers()


@pytest.fixture
def server():
    """在随机本机端口启动服务，并确保用例结束后停止。"""
    instance = LogStreamServer(port=0)
    instance.start()
    yield instance
    instance.stop()


def test_client_receives_complete_model_event(server):
    """真实客户端应收到字段完整且 owner 正确的模型日志事件。"""

    async def scenario():
        async with websockets.connect(f"ws://{server.host}:{server.port}") as client:
            await _wait_for_subscribers(1)
            TotLogStream.add_model_log(12, "thought", {"text": "hello"})
            return json.loads(await asyncio.wait_for(client.recv(), timeout=1))

    message = asyncio.run(scenario())
    assert message == {
        "status": "data",
        "event": {
            "ts": 12,
            "owner": "model",
            "type": "thought",
            "item": {"text": "hello"},
        },
    }


def test_multiple_clients_receive_same_event(server):
    """两个连接应通过各自队列收到同一个代理日志事件。"""

    async def scenario():
        url = f"ws://{server.host}:{server.port}"
        async with (
            websockets.connect(url) as first,
            websockets.connect(url) as second,
        ):
            await _wait_for_subscribers(2)
            TotLogStream.add_agent_log(8, "action", "move", 1)
            return await asyncio.gather(first.recv(), second.recv())

    first_message, second_message = asyncio.run(scenario())
    assert json.loads(first_message) == json.loads(second_message)
    assert json.loads(first_message)["event"]["owner"] == "agent_1"


def test_disconnected_client_is_unsubscribed(server):
    """客户端关闭后应自动退订，后续日志追加仍正常。"""

    async def scenario():
        async with websockets.connect(f"ws://{server.host}:{server.port}"):
            await _wait_for_subscribers(1)
        await _wait_for_subscribers(0)

    asyncio.run(scenario())
    TotLogStream.add_model_log(1, "thought", "after-close")
    assert _subscriber_count() == 0
    assert TotLogStream.model_log[-1]["item"] == "after-close"


def test_import_without_start_keeps_tot_log_stream_behavior(initialized_log):
    """仅构造但不启动服务时，不应创建订阅或改变文件日志行为。"""
    instance = LogStreamServer(port=0)
    TotLogStream.add_model_log(3, "thought", "offline")
    TotLogStream.write_log()

    assert not instance.is_running
    assert _subscriber_count() == 0
    lines = (initialized_log / "model.txt").read_text().splitlines()
    assert json.loads(lines[-1])["item"] == "offline"


def test_start_and_stop_are_idempotent_and_restartable():
    """重复启停不报错，停止后的实例可重新启动并继续转发。"""
    server = LogStreamServer(port=0)
    try:
        server.start()
        server.start()
        assert server.is_running
        server.stop()
        server.stop()
        assert not server.is_running

        server.start()
        assert server.is_running

        async def scenario():
            async with websockets.connect(f"ws://{server.host}:{server.port}") as client:
                await _wait_for_subscribers(1)
                TotLogStream.add_model_log(5, "restart", "ok")
                return json.loads(await asyncio.wait_for(client.recv(), timeout=1))

        assert asyncio.run(scenario())["event"]["item"] == "ok"
    finally:
        server.stop()


def test_stop_closes_connected_client(server):
    """停止服务应主动断开现有客户端并清理其订阅。"""

    async def scenario():
        client = await websockets.connect(f"ws://{server.host}:{server.port}")
        await _wait_for_subscribers(1)
        await asyncio.to_thread(server.stop)
        with pytest.raises(ConnectionClosed):
            await client.recv()
        await _wait_for_subscribers(0)

    asyncio.run(scenario())
    assert not server.is_running
