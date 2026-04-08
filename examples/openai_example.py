"""
OpenAI LLM 接入示例

使用方法：
1. 复制 .env.example 为 .env
2. 填入你的 OpenAI API Key
3. 运行：python examples/openai_example.py
"""

import os
from dotenv import load_dotenv
from casevo.llm import OpenAI_LLM
from casevo.llm_interface import LLMConfig

# 加载环境变量
load_dotenv()

def main():
    # 从环境变量读取配置
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")  # 可选
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    if not api_key:
        print("错误：请在 .env 文件中设置 OPENAI_API_KEY")
        return
    
    # 初始化 OpenAI LLM
    llm = OpenAI_LLM(
        api_key=api_key,
        base_url=base_url,
        default_model=model
    )
    
    # 基础对话
    print("=== 基础对话 ===")
    response = llm.send_message("你好，请简单介绍一下你自己。")
    print(f"回复：{response}\n")
    
    # 使用 LLMConfig 对话
    print("=== 使用 LLMConfig 对话 ===")
    config = LLMConfig(
        system="你是一个专业的社会学研究助手。",
        model=model,
        temperature=0.7
    )
    response = llm.chat(config, "请解释什么是多智能体模拟。")
    print(f"回复：{response}\n")
    
    # Embedding 示例
    print("=== Embedding 示例 ===")
    texts = ["人工智能", "机器学习", "深度学习"]
    embeddings = llm.send_embedding(texts)
    print(f"文本数量：{len(texts)}")
    print(f"向量维度：{len(embeddings[0])}")
    print(f"第一个向量（前5维）：{embeddings[0][:5]}...\n")


if __name__ == "__main__":
    main()
