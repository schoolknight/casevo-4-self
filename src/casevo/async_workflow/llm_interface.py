"""⚠️ DEPRECATED (2026-08-30)：本模块将由 Flovo 引擎（https://github.com/rgCASS/Flovo）
取代。请通过 casevo.flovo_client.FlovoClient 接入（见 examples/flovo_integration/）。
不再新增功能，仅修复致命 Bug。"""

from abc import ABCMeta, abstractmethod
from typing import Any

from casevo.llm_interface import LLMConfig, LLM_INTERFACE as SyncLLMInterface


# 异步工作流使用的 LLM 接口基类，兼容历史异步实现方式。
class LLM_INTERFACE(SyncLLMInterface, metaclass=ABCMeta):
    @abstractmethod
    def chat(self, config: LLMConfig, prompt: Any):
        pass

    @abstractmethod
    async def chat_async(self, config: LLMConfig, prompt: Any):
        pass

    @abstractmethod
    async def chat_stream(self, config: LLMConfig, prompt: Any, recall):
        pass

    @abstractmethod
    def intent_analysis(self, config: LLMConfig, prompt: Any, intent_tools: Any):
        pass

    @abstractmethod
    async def intent_analysis_async(
        self,
        config: LLMConfig,
        prompt: Any,
        intent_tools: Any,
    ):
        pass

    def send_message(self, prompt, json_flag=False):
        return self.chat(LLMConfig(system="", model=""), prompt)

    def send_message_by_config(self, prompt, llm_config: LLMConfig, json_flag: bool = False):
        return self.chat(llm_config, prompt)

    def send_embedding(self, text_list):
        raise NotImplementedError("send_embedding not implemented")

    def get_lang_embedding(self):
        raise NotImplementedError("get_lang_embedding not implemented")
