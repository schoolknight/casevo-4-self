"""
ChatGPT LLM实现模块
"""
import time
import json
from typing import List, Optional
from chromadb import Documents, EmbeddingFunction, Embeddings

from src.casevo.llm_interface import LLM_INTERFACE
from openai import OpenAI


class ChatGPTEmbedding(EmbeddingFunction):
    """ChatGPT嵌入函数，兼容ChromaDB"""

    def __init__(self, llm_instance, batch_size: int = 100):
        """
        初始化嵌入函数

        Args:
            llm_instance: ChatGPTLLM实例
            batch_size: 批处理大小
        """
        self.llm = llm_instance
        self.batch_size = batch_size

    def __call__(self, input: Documents) -> Embeddings:
        """
        处理文档嵌入

        Args:
            input: 文档列表

        Returns:
            嵌入向量列表
        """
        all_embeddings = []
        current_batch = []

        for text in input:
            current_batch.append(text)

            # 达到批处理大小时处理
            if len(current_batch) >= self.batch_size:
                embeddings = self.llm.send_embedding(current_batch)
                if embeddings:
                    all_embeddings.extend(embeddings)
                current_batch = []

        # 处理剩余的文本
        if current_batch:
            embeddings = self.llm.send_embedding(current_batch)
            if embeddings:
                all_embeddings.extend(embeddings)

        return all_embeddings


class ChatGPTLLM(LLM_INTERFACE):
    """ChatGPT LLM实现类"""

    def __init__(self, api_key: str, base_url: Optional[str] = None,
                 model: str = "gpt-4", embedding_model: str = "text-embedding-3-small",
                 temperature: float = 0.7, max_tokens: int = 2048):
        """
        初始化ChatGPT LLM

        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL（可选）
            model: 对话模型名称
            embedding_model: 嵌入模型名称
            temperature: 温度参数
            max_tokens: 最大token数
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.embedding_model = embedding_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 创建嵌入函数
        self.embedding_function = ChatGPTEmbedding(self)

    def send_message(self, prompt: str, json_flag: bool = False) -> Optional[str]:
        """
        发送消息到ChatGPT

        Args:
            prompt: 提示文本
            json_flag: 是否要求JSON格式响应

        Returns:
            响应文本，失败时返回None
        """
        try:
            # 构建请求参数
            messages = [{"role": "user", "content": prompt}]

            # 如果需要JSON格式，添加响应格式要求
            response_format = None
            if json_flag:
                response_format = {"type": "json_object"}

            # 发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=response_format
            )

            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"ChatGPT API调用失败: {str(e)}")

            # 简单的重试机制
            if "rate" in str(e).lower() or "limit" in str(e).lower():
                print("遇到限流，等待5秒后重试...")
                time.sleep(5)
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                    if response.choices and response.choices[0].message:
                        return response.choices[0].message.content.strip()
                except Exception as retry_error:
                    print(f"重试失败: {str(retry_error)}")

        return None

    def send_embedding(self, text_list: List[str]) -> Optional[List[List[float]]]:
        """
        获取文本嵌入向量

        Args:
            text_list: 文本列表

        Returns:
            嵌入向量列表，失败时返回None
        """
        try:
            # 分批处理，避免单次请求过大
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(text_list), batch_size):
                batch = text_list[i:i + batch_size]

                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )

                if response.data:
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)

                # 添加延迟避免限流
                if i + batch_size < len(text_list):
                    time.sleep(0.1)

            return all_embeddings if all_embeddings else None

        except Exception as e:
            print(f"ChatGPT嵌入API调用失败: {str(e)}")

            # 简单的重试机制
            if "rate" in str(e).lower() or "limit" in str(e).lower():
                print("遇到限流，等待5秒后重试...")
                time.sleep(5)
                try:
                    response = self.client.embeddings.create(
                        model=self.embedding_model,
                        input=text_list
                    )
                    if response.data:
                        return [item.embedding for item in response.data]
                except Exception as retry_error:
                    print(f"嵌入重试失败: {str(retry_error)}")

        return None

    def get_lang_embedding(self) -> ChatGPTEmbedding:
        """
        获取ChromaDB兼容的嵌入函数

        Returns:
            嵌入函数实例
        """
        return self.embedding_function