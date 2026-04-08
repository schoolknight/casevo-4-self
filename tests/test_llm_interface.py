"""llm_interface.py 模块单元测试。"""

from __future__ import annotations

import asyncio

import pytest

from casevo.llm_interface import LLMConfig, LLM_INTERFACE


class DummySyncLLM(LLM_INTERFACE):
    def __init__(self) -> None:
        self.messages = []

    def send_message(self, prompt, json_flag=False):
        self.messages.append(prompt)
        return f"ok:{prompt}"

    def send_embedding(self, text_list):
        return [[0.1] for _ in text_list]

    def get_lang_embedding(self):
        return None


def test_llm_config_to_dict_contains_all_fields():
    config = LLMConfig(system="sys", model="gpt", temperature=0.7, max_tokens=128)
    assert config.to_dict() == {
        "system": "sys",
        "model": "gpt",
        "temperature": 0.7,
        "max_tokens": 128,
    }


def test_chat_fallbacks_to_send_message_when_config_api_not_implemented():
    llm = DummySyncLLM()
    result = llm.chat(LLMConfig(system="sys", model="m"), "hello")
    assert result == "ok:hello"
    assert llm.messages[-1] == "hello"


def test_async_interfaces_raise_not_implemented_by_default():
    llm = DummySyncLLM()

    async def runner():
        await llm.chat_async(LLMConfig(system="sys", model="m"), "hello")

    with pytest.raises(NotImplementedError):
        asyncio.run(runner())
