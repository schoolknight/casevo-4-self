"""ChatGLM模块测试"""
import pytest
from unittest.mock import patch, Mock
from app.llm.chatglm import ChatGLMLLM
from llm.config import get_config

def test_chatglm_initialization():
    """测试ChatGLM初始化"""
    config = get_config('chatglm')
    llm = ChatGLMLLM(
        api_key=config['api_key'],
        model=config['model'],
        embedding_model=config['embedding_model']
    )

    assert llm.model == config['model']
    assert llm.embedding_model == config['embedding_model']

@patch('app.llm.chatglm.ZhipuAiClient')
def test_chatglm_send_message(mock_zhipu):
    """测试消息发送"""
    # 模拟API响应
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="模拟GLM响应"))]
    mock_response.usage = Mock(total_tokens=150)

    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_zhipu.return_value = mock_client

    # 测试消息发送
    config = get_config('chatglm')
    llm = ChatGLMLLM(
        api_key=config['api_key'],
        model=config['model'],
        embedding_model=config['embedding_model']
    )
    response = llm.send_message("你好")

    assert response == "模拟GLM响应"
    mock_client.chat.completions.create.assert_called_once()

@patch('app.llm.chatglm.ZhipuAiClient')
def test_chatglm_send_embedding(mock_zhipu):
    """测试文本嵌入"""
    # 模拟嵌入响应
    mock_embedding = Mock()
    mock_embedding.embedding = [0.1, 0.2, 0.3, 0.4] * 256

    mock_response = Mock()
    mock_response.data = [mock_embedding]

    mock_client = Mock()
    mock_client.embeddings.create.return_value = mock_response
    mock_zhipu.return_value = mock_client

    # 测试嵌入生成
    config = get_config('chatglm')
    llm = ChatGLMLLM(
        api_key=config['api_key'],
        model=config['model'],
        embedding_model=config['embedding_model']
    )
    embedding = llm.send_embedding("测试文本")

    # 检查返回的是嵌套列表结构
    assert isinstance(embedding, list)
    assert len(embedding) == 1  # 单个文本返回一个向量
    assert len(embedding[0]) == 1024  # 向量维度
    mock_client.embeddings.create.assert_called_once()
