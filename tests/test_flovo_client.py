"""FlovoClient 的 fake WebSocket 单元测试。"""

from __future__ import annotations

import asyncio
import json

import pytest

from casevo.flovo_client import FlovoClient, FlovoError


def envelope(workflow: str, command: str, message_id=None, info=None) -> str:
    return json.dumps(
        {
            "type": "service",
            "workflow": workflow,
            "cmd": command,
            "message_id": message_id,
            "info": {} if info is None else info,
            "resource": None,
        }
    )


class FakeWebSocket:
    def __init__(self, messages: list[object]):
        self.messages = list(messages)
        self.sent: list[dict] = []
        self.closed = False

    async def recv(self):
        if not self.messages:
            await asyncio.Future()
        return self.messages.pop(0)

    async def send(self, payload: str):
        self.sent.append(json.loads(payload))

    async def close(self):
        self.closed = True


def run(coro):
    return asyncio.run(coro)


def test_send_input_envelope_contains_protocol_fields(monkeypatch):
    ws = FakeWebSocket(
        [
            envelope("demo", "connect_ok", 0, {"accepted": True}),
            envelope("demo", "init_ok", 1, {"accepted": True}),
            envelope("demo", "workflow_finished"),
        ]
    )

    async def connect(_url):
        return ws

    monkeypatch.setattr("casevo.flovo_client.websockets.connect", connect)
    result = run(FlovoClient(timeout=0.1).run_workflow("demo", {"temperature": 0.2}, {"prompt": "hi"}))

    assert result == {}
    assert ws.sent[0]["cmd"] == "init_report"
    request = ws.sent[1]
    assert request == {
        "type": "service",
        "workflow": "demo",
        "cmd": "send_input",
        "message_id": 2,
        "info": {"temperature": 0.2, "prompt": "hi"},
        "resource": None,
    }


def test_run_workflow_parses_single_output(monkeypatch):
    ws = FakeWebSocket(
        [
            envelope("demo", "connect_ok", 0),
            envelope("demo", "init_ok", 1),
            envelope("demo", "output", info={"answer": 42}),
            envelope("demo", "workflow_finished"),
        ]
    )

    async def connect(_url):
        return ws

    monkeypatch.setattr("casevo.flovo_client.websockets.connect", connect)
    assert run(FlovoClient(timeout=0.1).run_workflow("demo", {}, {"x": 1})) == {"answer": 42}


def test_mismatched_init_message_is_ignored(monkeypatch, caplog):
    ws = FakeWebSocket(
        [
            envelope("demo", "connect_ok", 0),
            envelope("demo", "init_ok", 99),
            envelope("demo", "init_ok", 1),
            envelope("demo", "output", info={"ok": True}),
            envelope("demo", "workflow_finished"),
        ]
    )

    async def connect(_url):
        return ws

    monkeypatch.setattr("casevo.flovo_client.websockets.connect", connect)
    with caplog.at_level("WARNING"):
        result = run(FlovoClient(timeout=0.1).run_workflow("demo", {}, {}))
    assert result == {"ok": True}
    assert "mismatched message_id" in caplog.text


def test_stream_callback_receives_data_then_finish(monkeypatch):
    ws = FakeWebSocket(
        [
            envelope("demo", "connect_ok", 0),
            envelope("demo", "init_ok", 1),
            envelope("demo", "output", info={"step": 1}),
            envelope("demo", "output", info={"step": 2}),
            envelope("demo", "workflow_finished"),
        ]
    )

    async def connect(_url):
        return ws

    monkeypatch.setattr("casevo.flovo_client.websockets.connect", connect)
    events = []
    result = run(FlovoClient(timeout=0.1).run_workflow_stream("demo", {}, {}, events.append))
    assert [event["status"] for event in events] == ["data", "data", "finish"]
    assert [event["content"] for event in events[:2]] == [{"step": 1}, {"step": 2}]
    assert events[-1]["content"] == result == [{"step": 1}, {"step": 2}]


def test_timeout_raises_flovo_error(monkeypatch):
    ws = FakeWebSocket([envelope("demo", "connect_ok", 0), envelope("demo", "init_ok", 1)])

    async def connect(_url):
        return ws

    monkeypatch.setattr("casevo.flovo_client.websockets.connect", connect)
    with pytest.raises(FlovoError, match="timed out"):
        run(FlovoClient(timeout=0.01).run_workflow("demo", {}, {}))


def test_connection_failure_retries_three_times(monkeypatch):
    attempts = 0
    sleeps = []

    async def connect(_url):
        nonlocal attempts
        attempts += 1
        raise OSError("offline")

    async def no_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr("casevo.flovo_client.websockets.connect", connect)
    monkeypatch.setattr("casevo.flovo_client.asyncio.sleep", no_sleep)
    with pytest.raises(FlovoError, match="after 3 attempts"):
        run(FlovoClient(timeout=0.01).run_workflow("demo", {}, {}))
    assert attempts == 3
    assert sleeps == [1, 2]
