"""prompt.py 模块单元测试。"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from casevo.llm_interface import LLMConfig
from casevo.prompt import PromptFactory


def test_prompt_factory_init_with_missing_folder_raises(dummy_llm):
    """验证：模板目录不存在时，工厂初始化抛出异常。"""
    with pytest.raises(Exception, match="prompt folder not exist"):
        PromptFactory("/path/not/exist", dummy_llm)


def test_get_template_with_missing_file_raises(tmp_path, dummy_llm):
    """验证：模板文件不存在时，get_template 抛出异常。"""
    factory = PromptFactory(str(tmp_path), dummy_llm)

    with pytest.raises(Exception, match="prompt file.*not exist"):
        factory.get_template("missing.txt")


def test_render_and_send_prompt_success(tmp_path, dummy_llm):
    """覆盖：模板加载、渲染变量注入、发送到 LLM 的完整流程。"""
    template = (
        "agent={{ agent.description }}|{{ agent.context }} "
        "model={{ model.context }} extra={{ extra.note }}"
    )
    (tmp_path / "greet.txt").write_text(template, encoding="utf-8")

    factory = PromptFactory(str(tmp_path), dummy_llm)
    prompt = factory.get_template("greet.txt")

    agent = SimpleNamespace(description="tester", context="agent-ctx")
    model = SimpleNamespace(context="model-ctx")

    result = prompt.send_prompt(ertra={"note": "ok"}, agent=agent, model=model)

    assert result == "mock-response:agent=tester|agent-ctx model=model-ctx extra=ok"
    assert dummy_llm.messages[-1] == "agent=tester|agent-ctx model=model-ctx extra=ok"


class DummyPromptAsyncLLM:
    def __init__(self) -> None:
        self.calls = []

    async def chat_async(self, config: LLMConfig, prompt):
        self.calls.append(("chat", config.model, prompt))
        return f"chat:{prompt}"

    async def chat_stream(self, config: LLMConfig, prompt, recall):
        self.calls.append(("chat_stream", config.model, prompt))
        if recall:
            recall("chunk")
        return f"stream:{prompt}"

    async def intent_analysis_async(self, config: LLMConfig, prompt, intent_tools):
        self.calls.append(("intent_analysis", config.model, prompt, intent_tools))
        return {"intent": "ok"}

    def send_message(self, prompt_text: str):
        return f"sync:{prompt_text}"


def test_build_prompt_chat_async_success(tmp_path):
    (tmp_path / "chat.txt").write_text("{{ config.system }}-{{ params.name }}", encoding="utf-8")
    llm = DummyPromptAsyncLLM()
    factory = PromptFactory(str(tmp_path), llm)
    prompt = factory.build_prompt("chat", "chat.txt")

    async def runner():
        return await prompt.send_prompt(LLMConfig(system="sys", model="m"), {"name": "alice"})

    result = asyncio.run(runner())
    assert result == "chat:sys-alice"
    assert llm.calls[-1] == ("chat", "m", "sys-alice")
