"""Casevo 调用真实 Flovo ``agent_dialog`` 工作流的集成测试。"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import pytest
import websockets

from casevo.context_manager import ContextManager
from casevo.flovo_client import FlovoClient

WORKFLOW_NAME = "agent_dialog"
DEFAULT_FLOVO_URL = "ws://127.0.0.1:8090"
QUESTION_INPUTS = {
    "user_id": "user-integration",
    "session_id": "session-integration",
    "question": "What can Flovo do?",
}


def _workflow_url(base_url: str, workflow_name: str) -> str:
    """将工作流名称追加到 Flovo WebSocket 基础地址。"""
    parsed = urlsplit(base_url)
    path = f"{parsed.path.rstrip('/')}/{quote(workflow_name, safe='')}"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))


async def _probe_flovo() -> None:
    """短连接到 agent_dialog，并确认服务返回 connect_ok。"""
    base_url = os.getenv("FLOVO_WS_URL", DEFAULT_FLOVO_URL)
    websocket = await asyncio.wait_for(
        websockets.connect(_workflow_url(base_url, WORKFLOW_NAME)),
        timeout=0.5,
    )
    try:
        message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
        envelope = json.loads(message)
        if envelope.get("cmd") != "connect_ok":
            raise RuntimeError("Flovo did not return connect_ok")
    finally:
        await websocket.close()


@pytest.fixture(scope="module", autouse=True)
def require_flovo_server() -> None:
    """Flovo 服务或 agent_dialog 工作流不可用时跳过本模块。"""
    try:
        asyncio.run(_probe_flovo())
    except Exception:
        pytest.skip(
            "Flovo ws_server not running "
            "(start with cargo run -p flovo-ws --example server ...)"
        )


def _content_text(value: Any) -> str:
    """递归提取输出中的文本，兼容单 output 和多 output 汇总结果。"""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_content_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_content_text(item) for item in value)
    return "" if value is None else str(value)


async def _run_sync(inputs: dict[str, str], context: dict | None = None) -> Any:
    """使用独立客户端执行一次同步工作流并确保关闭连接。"""
    client = FlovoClient(timeout=10)
    try:
        return await client.run_workflow(WORKFLOW_NAME, {}, inputs, context=context)
    finally:
        await client.close()


@pytest.mark.integration
def test_sync_execution_returns_output() -> None:
    result = asyncio.run(_run_sync(QUESTION_INPUTS))

    assert result
    assert "mock" in _content_text(result).lower()


@pytest.mark.integration
def test_stream_execution_receives_data_then_finish() -> None:
    async def run_stream_scenario() -> tuple[Any, Any, list[dict]]:
        sync_result = await _run_sync(QUESTION_INPUTS)
        client = FlovoClient(timeout=10)
        events: list[dict] = []
        try:
            stream_result = await client.run_workflow_stream(
                WORKFLOW_NAME,
                {},
                QUESTION_INPUTS,
                events.append,
            )
        finally:
            await client.close()
        return sync_result, stream_result, events

    sync_result, stream_result, events = asyncio.run(run_stream_scenario())

    data_events = [event for event in events if event.get("status") == "data"]
    assert data_events
    assert events[-1] == {"status": "finish", "content": stream_result}
    assert stream_result == sync_result
    actual_data = (
        data_events[0]["content"]
        if len(data_events) == 1
        else [event["content"] for event in data_events]
    )
    assert actual_data == stream_result


@pytest.mark.integration
def test_condition_two_paths() -> None:
    async def run_condition_scenario() -> tuple[Any, Any]:
        llm_result = await _run_sync(QUESTION_INPUTS)
        fallback_result = await _run_sync({**QUESTION_INPUTS, "question": ""})
        return llm_result, fallback_result

    llm_result, fallback_result = asyncio.run(run_condition_scenario())

    assert "mock" in _content_text(llm_result).lower()
    assert "[fallback]" in _content_text(fallback_result).lower()


@pytest.mark.integration
def test_send_input_with_context_completes_workflow() -> None:
    """验证 ContextManager 到 FlovoClient send_input 的真实传递链路。

    Flovo 的 build_prompt 节点会读取 ``context.<field>`` 并将画像字段拼入 prompt，
    因此这里验证上下文影响了最终输出。
    """
    context = ContextManager(
        initial_context={"user_name": "alice", "tone": "formal"}
    ).to_dict()
    result = asyncio.run(_run_sync({**QUESTION_INPUTS}, context=context))

    assert result
    result_text = _content_text(result).lower()
    assert "alice" in result_text
    assert "formal" in result_text


@pytest.mark.integration
def test_send_input_without_context_degrades_to_mock() -> None:
    """验证不传上下文时仍保持 mock 降级行为。"""
    result = asyncio.run(_run_sync(QUESTION_INPUTS))

    assert result
    assert "[mock]" in _content_text(result).lower()


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("FLOVO_LLM_API_KEY") is None,
    reason="FLOVO_LLM_API_KEY not set",
)
def test_real_llm_execution_when_configured() -> None:
    """配置密钥时验证 Flovo 的真实 LLM 链路可返回结果。"""
    result = asyncio.run(_run_sync(QUESTION_INPUTS))

    assert result
    assert "[mock]" not in _content_text(result).lower()
