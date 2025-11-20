"""ChatGPT模块测试"""
import pytest
from unittest.mock import patch, Mock
from app.llm.chatgpt import ChatGPTLLM
from llm.config import get_config

def test_chatgpt_initialization():
    """测试ChatGPT初始化"""
    config = get_config('chatgpt')
    llm = ChatGPTLLM(
        api_key=config['api_key'],
        base_url=config['base_url'],
        model=config['model'],
        embedding_model=config['embedding_model']
    )

    assert llm.model == config['model']
    assert llm.embedding_model == config['embedding_model']

@patch('app.llm.chatgpt.OpenAI')
def test_chatgpt_send_message(mock_openai):
    """测试消息发送"""
    # 模拟API响应
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="模拟响应"))]
    mock_response.usage = Mock(total_tokens=100)

    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    # 测试消息发送
    config = get_config('chatgpt')
    llm = ChatGPTLLM(
        api_key=config['api_key'],
        base_url=config['base_url'],
        model=config['model'],
        embedding_model=config['embedding_model']
    )
    response = llm.send_message("你好")

    assert response == "模拟响应"
    mock_client.chat.completions.create.assert_called_once()

@patch('app.llm.chatgpt.OpenAI')
def test_chatgpt_send_embedding(mock_openai):
    """测试文本嵌入"""
    # 模拟嵌入响应
    mock_embedding = Mock()
    mock_embedding.embedding = [0.1, 0.2, 0.3] * 512

    mock_response = Mock()
    mock_response.data = [mock_embedding]

    mock_client = Mock()
    mock_client.embeddings.create.return_value = mock_response
    mock_openai.return_value = mock_client

    # 测试嵌入生成
    config = get_config('chatgpt')
    llm = ChatGPTLLM(
        api_key=config['api_key'],
        base_url=config['base_url'],
        model=config['model'],
        embedding_model=config['embedding_model']
    )
    embedding = llm.send_embedding("测试文本")

    # 检查返回的是嵌套列表结构
    assert isinstance(embedding, list)
    assert len(embedding) == 1  # 单个文本返回一个向量
    assert len(embedding[0]) == 1536  # 向量维度
    mock_client.embeddings.create.assert_called_once()
