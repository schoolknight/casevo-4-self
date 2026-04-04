from abc import abstractmethod, ABCMeta
from typing import List, Dict, Any, Optional


# LLM 接口基类
class LLM_INTERFACE(metaclass=ABCMeta):
    """
    大语言模型抽象接口基类。

    用户需继承本类并实现所有抽象方法，以接入具体的 LLM 后端（如 OpenAI、Claude 等）。
    所有构造参数均提供默认值，现有子类无需修改即可正常实例化。
    """

    def __init__(
        self,
        model_name: str = "",
        system_prompt: str = "",
        model_params: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化 LLM 接口基类。

        Args:
            model_name (str): 大模型名称，例如 "gpt-4o"、"claude-3-5-sonnet-20241022"。
                              默认为空字符串，子类可在 __init__ 中指定具体模型。
            system_prompt (str): 全局系统提示词，将在每次请求时注入 system 角色。
                                  默认为空字符串（不注入系统提示词）。
            model_params (dict): 生成参数字典，包含 temperature、top_p、max_tokens 等。
                                  默认为空字典，子类可按需覆盖或扩展。
        """
        self.model_name: str = model_name
        self.system_prompt: str = system_prompt
        self.model_params: Dict[str, Any] = model_params if model_params is not None else {}

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

    @abstractmethod
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
        pass
