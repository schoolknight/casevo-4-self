"""GLM LLM 实现。"""

from __future__ import annotations

from typing import Optional

from casevo.llm.openai_llm import OpenAI_LLM


class GLM_LLM(OpenAI_LLM):
    """智谱 GLM 的 OpenAI 兼容实现。"""

    GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(
        self,
        api_key: str,
        default_model: str = "glm-4",
        base_url: Optional[str] = GLM_BASE_URL,
    ) -> None:
        """
        初始化 GLM 客户端。

        Args:
            api_key (str): 智谱 API Key。
            default_model (str): 默认聊天模型。
            base_url (Optional[str]): 自定义端点，默认智谱 OpenAI 兼容端点。
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            embedding_model="embedding-3",
        )
