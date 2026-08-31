"""Flovo ``agent_dialog`` 集成示例。

运行方式：先启动 Flovo WebSocket 服务，再执行
``python examples/flovo_integration/agent_dialog_demo.py``。
示例覆盖同步调用、上下文传入、流式 data/finish 回调，以及有问题和空问题两条 condition 分支。
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from casevo.flovo_client import FlovoClient, FlovoError

WORKFLOW_NAME = "agent_dialog"
BASE_INPUTS = {
    "user_id": "user-demo",
    "session_id": "session-demo",
}


def _content_text(value: Any) -> str:
    """递归提取工作流结果中的文本，兼容单 output 和多 output 结果。"""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_content_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_content_text(item) for item in value)
    return "" if value is None else str(value)


def _print_llm_configuration() -> None:
    """说明真实 LLM 的环境变量配置状态，不打印密钥内容。"""
    print("=== LLM configuration ===")
    if os.getenv("FLOVO_LLM_API_KEY"):
        print("已检测到 FLOVO_LLM_API_KEY，llm_call 将使用真实 OpenAI 兼容接口。")
    else:
        print("未配置 FLOVO_LLM_API_KEY，llm_call 将自动降级为 mock。")
    print(
        "可选配置：FLOVO_LLM_BASE_URL（默认 https://api.openai.com/v1）、"
        "FLOVO_LLM_MODEL（默认 gpt-4o-mini）。"
    )


async def main() -> None:
    """依次演示同步、流式和空问题兜底调用。"""
    client = FlovoClient()
    question_inputs = {
        **BASE_INPUTS,
        "question": "What can Flovo do?",
    }
    fallback_inputs = {
        **BASE_INPUTS,
        "question": "",
    }
    context = {"user_name": "alice", "tone": "formal"}

    try:
        _print_llm_configuration()
        print("\n=== Sync: non-empty question (LLM path) ===")
        sync_result = await client.run_workflow(WORKFLOW_NAME, {}, question_inputs)
        print("result:", sync_result)

        print("\n=== Sync: context bridge ===")
        print("调用方式：run_workflow(..., context={'user_name': 'alice', 'tone': 'formal'})")
        context_result = await client.run_workflow(
            WORKFLOW_NAME, {}, question_inputs, context=context
        )
        print("result:", context_result)
        context_text = _content_text(context_result).lower()
        if "alice" in context_text and "formal" in context_text:
            print("说明：上下文已影响输出，结果包含 user_name=alice 与 tone=formal。")
        else:
            print(
                "提示：输出未包含 alice/formal，请确认 Flovo 侧已合入 R024 的 build_prompt 节点。"
            )

        print("\n=== Stream: non-empty question (data -> finish) ===")

        def print_event(event: dict) -> None:
            """打印 FlovoClient 转发的单个流式事件。"""
            print("event:", event)

        await client.run_workflow_stream(
            WORKFLOW_NAME,
            {},
            question_inputs,
            print_event,
        )

        print("\n=== Sync: empty question (fallback path) ===")
        fallback_result = await client.run_workflow(WORKFLOW_NAME, {}, fallback_inputs)
        print("result:", fallback_result)
    except FlovoError as exc:
        print(f"Flovo request failed: {exc}")
        print("Please confirm the Flovo ws_server is running and FLOVO_WS_URL is correct.")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
