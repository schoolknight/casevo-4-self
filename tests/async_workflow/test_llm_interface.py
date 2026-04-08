"""async_workflow/llm_interface.py 模块单元测试。"""

from __future__ import annotations

from casevo.async_workflow.llm_interface import LLMConfig, LLM_INTERFACE


class DummyAsyncWorkflowLLM(LLM_INTERFACE):
    def chat(self, config: LLMConfig, prompt):
        return f"chat:{prompt}"

    async def chat_async(self, config: LLMConfig, prompt):
        return f"chat_async:{prompt}"

    async def chat_stream(self, config: LLMConfig, prompt, recall):
        if recall:
            recall("chunk")
        return f"chat_stream:{prompt}"

    def intent_analysis(self, config: LLMConfig, prompt, intent_tools):
        return {"prompt": prompt, "intent_tools": intent_tools}

    async def intent_analysis_async(self, config: LLMConfig, prompt, intent_tools):
        return {"prompt": prompt, "intent_tools": intent_tools}


def test_async_workflow_llm_interface_keeps_legacy_contract():
    llm = DummyAsyncWorkflowLLM()
    config = LLMConfig(system="sys", model="m", temperature=0.5, max_tokens=16)

    assert llm.send_message("hello") == "chat:hello"
    assert llm.send_message_by_config("hello2", config) == "chat:hello2"
    assert config.to_dict()["temperature"] == 0.5
    assert config.to_dict()["max_tokens"] == 16
