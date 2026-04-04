from abc import abstractmethod, ABCMeta
from typing import List, Dict, Any, Optional

from dataclasses import dataclass

@dataclass
class LLMConfig:
    system: str
    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    def to_dict(self):
        return {
            "system": self.system,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }



# LLM 接口基类
class LLM_INTERFACE(metaclass=ABCMeta):
    """
    大语言模型抽象接口基类。

    用户需继承本类并实现所有抽象方法，以接入具体的 LLM 后端（如 OpenAI、Claude 等）。
    所有构造参数均提供默认值，现有子类无需修改即可正常实例化。
    """


    @abstractmethod
    def send_message(self, prompt, json_flag=False):
        """
        发送单轮对话消息并返回模型响应文本。

        Args:
            prompt: 消息内容，可为字符串或消息列表（具体格式由子类决定）。
            json_flag (bool): 是否要求模型以 JSON 格式返回。默认 False。

        Returns:
            str: 模型返回的文本响应。
        """
        pass

    def send_message_by_config(
        self, prompt, llm_config: LLMConfig, json_flag: bool = False
    ):
        """
        使用指定 LLMConfig 发送单轮对话消息并返回模型响应文本。

        Args:
            prompt: 消息内容，可为字符串或消息列表（具体格式由子类决定）。
            llm_config (LLMConfig): 本次请求使用的模型配置。
            json_flag (bool): 是否要求模型以 JSON 格式返回。默认 False。

        Returns:
            str: 模型返回的文本响应。
        """
        raise NotImplementedError("send_message_by_config not implemented")

    @abstractmethod
    def send_embedding(self, text_list):
        """
        对文本列表执行向量嵌入，返回嵌入向量列表。

        Args:
            text_list (List[str]): 需要嵌入的文本列表。

        Returns:
            List[List[float]]: 对应的嵌入向量列表。
        """
        pass

    @abstractmethod
    def get_lang_embedding(self):
        """
        获取与 ChromaDB 兼容的 langchain EmbeddingFunction 工具类实例。

        Returns:
            EmbeddingFunction: ChromaDB 可直接使用的 embedding function 对象。
        """
        pass

    def send_message_with_tools(
        self,
        prompt: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        json_flag: bool = False,
    ):
        """
        发送带工具定义的对话请求，支持大模型工具调用（Function Calling / Tool Use）。

        Args:
            prompt (List[Dict[str, Any]]): 消息列表，每个元素为包含 role 和 content 的字典，
                                           例如 [{"role": "user", "content": "查询天气"}]。
            tools (List[Dict[str, Any]]): 工具定义列表，每个元素描述一个可调用工具的名称、
                                          描述及参数 schema，格式遵循所用 LLM 的工具调用规范。
            json_flag (bool): 是否要求模型以 JSON 格式返回最终文本响应。默认 False。

        Returns:
            模型的工具调用响应或文本响应（具体类型由子类实现决定）。
        """
        raise NotImplementedError("send_message_with_tools not implemented")
