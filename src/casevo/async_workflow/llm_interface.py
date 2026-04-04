from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMConfig:
    system: str
    model: str

    def to_dict(self) -> dict[str, str]:
        return {
            "system": self.system,
            "model": self.model,
        }


# 异步工作流使用的 LLM 接口基类，与同步接口完全隔离。
class LLM_INTERFACE(metaclass=ABCMeta):
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
