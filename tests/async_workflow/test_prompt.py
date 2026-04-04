"""async_workflow/prompt.py 模块单元测试。"""

from __future__ import annotations

import asyncio

from casevo.async_workflow.llm_interface import LLMConfig, LLM_INTERFACE
from casevo.async_workflow.prompt import PromptFactory


class DummyAsyncLLM(LLM_INTERFACE):
    def __init__(self) -> None:
        self.chat_messages: list[str] = []
        self.intent_calls: list[tuple[str, list[str]]] = []

    def chat(self, config: LLMConfig, prompt):
        return prompt

    async def chat_async(self, config: LLMConfig, prompt):
        self.chat_messages.append(prompt)
        return f"chat:{prompt}"

    async def chat_stream(self, config: LLMConfig, prompt, recall):
        if recall:
            recall("chunk")
        return f"stream:{prompt}"

    def intent_analysis(self, config: LLMConfig, prompt, intent_tools):
        return {"prompt": prompt, "intent_tools": intent_tools}

    async def intent_analysis_async(self, config: LLMConfig, prompt, intent_tools):
        self.intent_calls.append((prompt, intent_tools))
        return {"ok": True}


def test_build_prompt_with_missing_file_raises(tmp_path):
    factory = PromptFactory(str(tmp_path), DummyAsyncLLM())
    try:
        factory.build_prompt("chat", "missing.txt")
    except Exception as exc:
        assert "prompt file" in str(exc)
    else:
        raise AssertionError("should raise missing prompt file")


def test_chat_prompt_render_and_send_success(tmp_path):
    (tmp_path / "chat.txt").write_text("{{ config.system }}-{{ params.name }}", encoding="utf-8")

    llm = DummyAsyncLLM()
    factory = PromptFactory(str(tmp_path), llm)
    prompt = factory.build_prompt("chat", "chat.txt")

    async def runner():
        return await prompt.send_prompt(LLMConfig(system="sys", model="m"), {"name": "alice"})

    result = asyncio.run(runner())
    assert result == "chat:sys-alice"
    assert llm.chat_messages[-1] == "sys-alice"
