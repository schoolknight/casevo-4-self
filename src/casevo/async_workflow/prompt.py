from __future__ import annotations

import os
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

from .llm_interface import LLMConfig, LLM_INTERFACE


class PromptBase:
    def __init__(self, tar_template, tar_factory: "PromptFactory"):
        self.template = tar_template
        self.factory = tar_factory

    def __get_prompt__(self, config: Optional[LLMConfig], tar_dict: Optional[dict[str, Any]]):
        tmp_dict = {
            "config": config.to_dict() if config else {},
            "params": tar_dict or {},
        }
        return self.template.render(**tmp_dict)

    async def send_prompt(self, config=None, params=None, recall=None):
        raise NotImplementedError("This method should be implemented in subclasses")


class PromptChat(PromptBase):
    async def send_prompt(self, config: Optional[LLMConfig] = None, params=None):
        prompt_text = self.__get_prompt__(config, params)
        return await self.factory.__send_message__("chat", config, prompt_text)


class PromptChatStream(PromptBase):
    async def send_prompt(self, config: Optional[LLMConfig] = None, params=None, recall=None):
        prompt_text = self.__get_prompt__(config, params)
        return await self.factory.__send_message__("chat_stream", config, prompt_text, recall=recall)


class PromptIntentAnalysis(PromptBase):
    def __init__(self, tar_template, tar_factory: "PromptFactory", intents):
        super().__init__(tar_template, tar_factory)
        self.intents = intents

    async def send_prompt(self, config: Optional[LLMConfig] = None, params=None, recall=None):
        prompt_text = self.__get_prompt__(config, params)
        return await self.factory.__send_message__(
            "intent_analysis",
            config,
            prompt_text,
            intent=self.intents,
        )


# 异步 Prompt 工厂。
class PromptFactory:
    def __init__(self, tar_folder: str, llm: LLM_INTERFACE):
        self.prompt_folder = tar_folder
        if not os.path.exists(tar_folder):
            raise Exception("prompt folder not exist")
        self.env = Environment(loader=FileSystemLoader(tar_folder))
        self.llm = llm

    def build_prompt(self, prompt_type: str, template_name: str, intents=None):
        tar_file = os.path.join(self.prompt_folder, template_name)
        if not os.path.exists(tar_file):
            raise Exception("prompt file %s not exist" % template_name)

        res_temp = self.env.get_template(template_name)

        if prompt_type == "chat":
            return PromptChat(res_temp, self)
        if prompt_type == "chat_stream":
            return PromptChatStream(res_temp, self)
        if prompt_type == "intent_analysis":
            return PromptIntentAnalysis(res_temp, self, intents)

        raise Exception("prompt type %s not support" % prompt_type)

    async def __send_message__(self, msg_type, config, prompt, recall=None, intent=None):
        if msg_type == "chat":
            return await self.llm.chat_async(config, prompt)

        if msg_type == "chat_stream":
            return await self.llm.chat_stream(config, prompt, recall)

        if msg_type == "intent_analysis":
            return await self.llm.intent_analysis_async(config, prompt, intent)

        raise Exception("send message type not support")
