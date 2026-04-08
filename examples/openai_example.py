"""OpenAI 接入示例：演示聊天、配置化聊天与 Embedding。"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from casevo.llm import OpenAI_LLM
from casevo.llm_interface import LLMConfig


def _require_env(name: str) -> str:
    """读取必填环境变量，缺失时给出明确错误。"""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"缺少环境变量 {name}，请先配置 examples/.env 或系统环境变量。")
    return value


def main() -> None:
    # 从当前目录或上级目录加载 .env，避免硬编码密钥。
    load_dotenv()

    api_key = _require_env("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o"

    # 初始化 OpenAI 客户端（支持自定义 base_url 与 model）。
    llm = OpenAI_LLM(api_key=api_key, base_url=base_url, default_model=model)

    # 1) 基础对话：直接传字符串 prompt。
    basic_reply = llm.send_message("请用一句话介绍 Casevo。")
    print("[基础对话]", basic_reply)

    # 2) 使用 LLMConfig：可显式控制 system/model/temperature/max_tokens。
    config = LLMConfig(
        system="你是一个简洁、准确的技术助理。",
        model=model,
        temperature=0.2,
        max_tokens=128,
    )
    config_reply = llm.send_message_by_config(
        "请给出三条编写高质量 Python 代码的建议。",
        llm_config=config,
    )
    print("[LLMConfig 对话]", config_reply)

    # 3) Embedding：批量文本向量化，返回二维浮点数组。
    embedding_vectors = llm.send_embedding(["Casevo", "LLM integration example"])
    print("[Embedding] 向量数量:", len(embedding_vectors))
    if embedding_vectors:
        print("[Embedding] 单条向量维度:", len(embedding_vectors[0]))


if __name__ == "__main__":
    main()
