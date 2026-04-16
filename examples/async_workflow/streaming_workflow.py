"""异步流式工作流示例：展示 BaseStreamNode + recall 的关键用法。"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any

from casevo.async_workflow import BaseStepNode, BaseStreamNode, LLMConfig, PromptFactory, WorkFlow
from casevo.async_workflow.llm_interface import LLM_INTERFACE


class MockStreamLLM(LLM_INTERFACE):
    """最小可运行的流式 LLM 示例实现。

    说明:
        仅用于演示 chat_stream 回调逻辑，不依赖真实模型服务。
    """

    def chat(self, config: LLMConfig, prompt: Any):
        return f"chat:{prompt}"

    async def chat_async(self, config: LLMConfig, prompt: Any):
        return f"chat_async:{prompt}"

    async def chat_stream(self, config: LLMConfig, prompt: Any, recall):
        """模拟 LLM 流式输出，将 token 逐个回调。"""
        for token in ["你好", "，", "异步", "工作流", "！"]:
            if recall:
                recall(token)
            await asyncio.sleep(0)
        return "[stream done]"

    def intent_analysis(self, config: LLMConfig, prompt: Any, intent_tools: Any):
        return {"intent": "demo"}

    async def intent_analysis_async(self, config: LLMConfig, prompt: Any, intent_tools: Any):
        return {"intent": "demo_async"}


class StreamStartNode(BaseStreamNode):
    """流式起始节点：通过 PromptFactory 调用 chat_stream 并持续写入 stream 输出。"""

    def __init__(self, config: dict[str, Any], workflow: WorkFlow):
        super().__init__(config, workflow)
        self.input_parameters = {"prompt": "step"}
        self.output_parameters = {"delta": "stream"}
        self.choices = ["next"]

    async def run(self, input_parameters: dict[str, Any] | None = None) -> bool:
        """执行流式节点。

        参数:
            input_parameters: 预留参数。
        返回:
            bool: True 表示执行完成。
        """
        await self.wait_for_event()
        user_prompt = await self.get_input("prompt")

        async def on_token(token: str) -> None:
            # 将 token 写入 stream 参数，供下游 continue/end 节点消费。
            await self.set_output("delta", token)

        def recall(token: str) -> None:
            # chat_stream 的回调是同步函数，这里转为异步任务执行。
            asyncio.create_task(on_token(token))

        stream_prompt = self.parent_workflow.prompt_factory.build_prompt("chat_stream", "stream_prompt.j2")
        config = LLMConfig(system="你是简洁助手", model="mock-stream")
        await stream_prompt.send_prompt(config=config, params={"message": user_prompt}, recall=recall)

        # 明确发送流结束标记，供下游节点退出消费循环。
        await self.set_output("delta", "<END>")
        self.set_choice("next")
        return True


class StreamCollectNode(BaseStepNode):
    """流式续接节点：消费 stream token 并聚合为最终文本。"""

    def __init__(self, config: dict[str, Any], workflow: WorkFlow):
        super().__init__(config, workflow)
        self.input_parameters = {"delta": "stream"}
        self.output_parameters = {"answer": "step"}
        self.choices = ["end"]

    async def run(self, input_parameters: dict[str, Any] | None = None) -> bool:
        """循环读取 stream 输入直到收到结束标记。"""
        await self.wait_for_event()

        chunks: list[str] = []
        while True:
            token = await self.get_input("delta")
            if token == "<END>":
                break
            chunks.append(token)
            print("[stream token]", token)

        await self.set_output("answer", "".join(chunks))
        self.set_choice("end")
        return True


def _create_prompt_factory() -> PromptFactory:
    """创建临时模板目录并初始化 PromptFactory。"""
    tmp_dir = Path(tempfile.mkdtemp(prefix="casevo_stream_prompt_"))
    (tmp_dir / "stream_prompt.j2").write_text(
        "{{ config.system }} | {{ params.message }}",
        encoding="utf-8",
    )
    return PromptFactory(str(tmp_dir), MockStreamLLM())


async def run_streaming_workflow(user_text: str) -> dict[str, Any]:
    """运行流式工作流并返回最终聚合结果。"""
    workflow = WorkFlow(name="stream_demo", prompt_factory=_create_prompt_factory())
    workflow.set_input_parameters({"prompt": "step"})

    stream_node = StreamStartNode(
        {
            "id": "s1",
            "node_name": "node_stream_start",
            "choice_map": {"next": "node_collect"},
            "attrs": {"desc": "stream producer"},
            "input_map": {"prompt": "start.prompt"},
            "stream_type": "start",
        },
        workflow,
    )
    collect_node = StreamCollectNode(
        {
            "id": "s2",
            "node_name": "node_collect",
            "choice_map": {"end": "finish"},
            "attrs": {"desc": "stream consumer"},
            "input_map": {"delta": "node_stream_start.delta"},
        },
        workflow,
    )

    stream_node.check_set_config()
    collect_node.check_set_config()

    workflow.set_nodes_list([stream_node, collect_node])
    workflow.set_start_node("node_stream_start")

    await workflow.set_input({"prompt": user_text})
    await workflow.run_all()
    return workflow.get_result()


def main() -> None:
    """通过 asyncio.run 启动流式工作流示例。"""
    result = asyncio.run(run_streaming_workflow("请简短问候"))
    print("[streaming_workflow] result:", result)  # 预期: {'answer': '你好，异步工作流！'}


if __name__ == "__main__":
    main()
