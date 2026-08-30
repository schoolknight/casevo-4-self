"""Flovo ``agent_dialog`` 集成示例。

运行方式：先启动 Flovo WebSocket 服务，再执行
``python examples/flovo_integration/agent_dialog_demo.py``。
示例覆盖同步调用、流式 data/finish 回调，以及有问题和空问题两条 condition 分支。
"""

from __future__ import annotations

import asyncio

from casevo.flovo_client import FlovoClient, FlovoError

WORKFLOW_NAME = "agent_dialog"
BASE_INPUTS = {
    "user_id": "user-demo",
    "session_id": "session-demo",
}


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

    try:
        print("\n=== Sync: non-empty question (LLM path) ===")
        sync_result = await client.run_workflow(WORKFLOW_NAME, {}, question_inputs)
        print("result:", sync_result)

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
