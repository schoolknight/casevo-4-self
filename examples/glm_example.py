"""GLM 接入示例：演示聊天、配置化聊天与 Embedding。"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from casevo.llm import GLM_LLM
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

    api_key = _require_env("GLM_API_KEY")
    model = os.getenv("GLM_MODEL", "").strip() or "glm-4"

    # 初始化 GLM 客户端：默认使用智谱 OpenAI 兼容端点。
    llm = GLM_LLM(api_key=api_key, default_model=model)

    # 1) 基础对话：直接传字符串 prompt。
    basic_reply = llm.send_message("请用一句话介绍 GLM 在中文任务中的优势。")
    print("[基础对话]", basic_reply)

    # 2) 使用 LLMConfig：显式传递系统提示和参数。
    config = LLMConfig(
        system="你是一个专注于工程实践的中文技术助理。",
        model=model,
        temperature=0.2,
        max_tokens=128,
    )
    config_reply = llm.send_message_by_config(
        "请给出两条在生产环境调用 LLM API 的安全建议。",
        llm_config=config,
    )
    print("[LLMConfig 对话]", config_reply)

    # 3) Embedding：GLM 默认使用 embedding-3 模型。
    embedding_vectors = llm.send_embedding(["Casevo", "GLM embedding example"])
    print("[Embedding] 向量数量:", len(embedding_vectors))
    if embedding_vectors:
        print("[Embedding] 单条向量维度:", len(embedding_vectors[0]))


if __name__ == "__main__":
    main()
