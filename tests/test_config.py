"""配置模块测试"""
import pytest
from llm.config import get_config, validate_config

def test_get_config():
    """测试配置获取"""
    # 测试ChatGPT配置
    chatgpt_config = get_config('chatgpt')
    assert chatgpt_config['model'] == 'gpt-4'
    assert chatgpt_config['embedding_model'] == 'text-embedding-3-small'
    assert chatgpt_config['api_key'] is not None

    # 测试ChatGLM配置
    chatglm_config = get_config('chatglm')
    assert chatglm_config['model'] == 'glm-4.6'
    assert chatglm_config['embedding_model'] == 'embedding-3'
    assert chatglm_config['api_key'] is not None

def test_validate_config():
    """测试配置验证"""
    # 测试有效配置
    assert validate_config('chatgpt') == True
    assert validate_config('chatglm') == True

    # 测试无效配置
    assert validate_config('invalid') == False
