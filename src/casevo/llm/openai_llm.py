"""OpenAI LLM 实现。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

try:
    from chromadb.api.types import EmbeddingFunction
except Exception:  # pragma: no cover - 测试环境可能使用 chromadb stub
    class EmbeddingFunction:  # type: ignore[override]
        """chromadb 不可用时的最小回退类型。"""

        pass

from casevo.llm_interface import LLMConfig, LLM_INTERFACE

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - 仅在未安装可选依赖时触发
    OpenAI = None  # type: ignore[assignment]


class OpenAIEmbeddingFunction(EmbeddingFunction):
    """兼容 ChromaDB 的 OpenAI EmbeddingFunction。"""

    def __init__(self, client: Any, model: str = "text-embedding-3-small") -> None:
        self.client = client
        self.model = model

    def __call__(self, input: Sequence[str]) -> List[List[float]]:
        response = self.client.embeddings.create(input=input, model=self.model)
        return [item.embedding for item in response.data]


class OpenAI_LLM(LLM_INTERFACE):
    """基于 OpenAI SDK 的 LLM 实现。"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o",
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        """
        初始化 OpenAI LLM 客户端。

        Args:
            api_key (str): OpenAI API Key。
            base_url (Optional[str]): 自定义端点地址。
            default_model (str): 默认聊天模型。
            embedding_model (str): 默认嵌入模型。
        """
        if OpenAI is None:
            raise ImportError(
                "openai dependency is required, please install with `pdm add openai`."
            )

        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)
        self.default_model = default_model
        self.embedding_model = embedding_model
        self.base_url = base_url

    @staticmethod
    def _normalize_messages(prompt: Any) -> List[Dict[str, Any]]:
        """将输入统一转换为 OpenAI chat messages 格式。"""
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        if isinstance(prompt, list):
            return prompt
        raise TypeError("prompt must be str or list[dict]")

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        """提取响应中的文本内容。"""
        message = response.choices[0].message
        content = getattr(message, "content", "")

        if isinstance(content, str):
            return content

        # 兼容多模态返回结构（content 可能为数组）
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                else:
                    text = getattr(item, "text", None)
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)

        return ""

    @staticmethod
    def _chat_kwargs_from_config(
        llm_config: LLMConfig,
        json_flag: bool,
    ) -> Dict[str, Any]:
        """将 LLMConfig 映射为 chat.completions 参数。"""
        kwargs: Dict[str, Any] = {"model": llm_config.model}
        if llm_config.temperature is not None:
            kwargs["temperature"] = llm_config.temperature
        if llm_config.max_tokens is not None:
            kwargs["max_tokens"] = llm_config.max_tokens
        if json_flag:
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    def send_message(self, prompt: Any, json_flag: bool = False) -> str:
        """
        发送单轮消息。

        Args:
            prompt (Any): 提示词（字符串或 messages 列表）。
            json_flag (bool): 是否要求 JSON 输出。

        Returns:
            str: 模型返回文本。
        """
        messages = self._normalize_messages(prompt)
        kwargs: Dict[str, Any] = {"model": self.default_model, "messages": messages}
        if json_flag:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return self._extract_response_text(response)

    def send_message_by_config(
        self,
        prompt: Any,
        llm_config: LLMConfig,
        json_flag: bool = False,
    ) -> str:
        """
        使用 LLMConfig 发送单轮消息。

        Args:
            prompt (Any): 提示词（字符串或 messages 列表）。
            llm_config (LLMConfig): 请求配置。
            json_flag (bool): 是否要求 JSON 输出。

        Returns:
            str: 模型返回文本。
        """
        messages = self._normalize_messages(prompt)
        if llm_config.system:
            messages = [{"role": "system", "content": llm_config.system}, *messages]

        kwargs = self._chat_kwargs_from_config(llm_config, json_flag)
        kwargs["messages"] = messages

        response = self.client.chat.completions.create(**kwargs)
        return self._extract_response_text(response)

    def send_message_with_tools(
        self,
        prompt: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        json_flag: bool = False,
    ) -> Dict[str, Any]:
        """
        发送带工具定义的消息请求。

        Args:
            prompt (List[Dict[str, Any]]): 对话消息列表。
            tools (List[Dict[str, Any]]): 工具定义。
            json_flag (bool): 是否要求 JSON 输出。

        Returns:
            Dict[str, Any]: 包含文本与工具调用信息的结果。
        """
        kwargs: Dict[str, Any] = {
            "model": self.default_model,
            "messages": self._normalize_messages(prompt),
            "tools": tools,
        }
        if json_flag:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)

        normalized_tool_calls = []
        if tool_calls:
            for call in tool_calls:
                function_obj = getattr(call, "function", None)
                normalized_tool_calls.append(
                    {
                        "id": getattr(call, "id", None),
                        "type": getattr(call, "type", None),
                        "function": {
                            "name": getattr(function_obj, "name", None),
                            "arguments": getattr(function_obj, "arguments", None),
                        },
                    }
                )

        return {
            "content": self._extract_response_text(response),
            "tool_calls": normalized_tool_calls,
            "raw_message": message,
        }

    def send_embedding(self, text_list: List[str]) -> List[List[float]]:
        """
        批量生成文本向量。

        Args:
            text_list (List[str]): 输入文本列表。

        Returns:
            List[List[float]]: 向量列表。
        """
        response = self.client.embeddings.create(input=text_list, model=self.embedding_model)
        return [item.embedding for item in response.data]

    def get_lang_embedding(self) -> OpenAIEmbeddingFunction:
        """
        返回 ChromaDB 可直接使用的 EmbeddingFunction。

        Returns:
            OpenAIEmbeddingFunction: EmbeddingFunction 实例。
        """
        return OpenAIEmbeddingFunction(client=self.client, model=self.embedding_model)
