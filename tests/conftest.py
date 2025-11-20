"""pytest配置和fixtures"""
import pytest
import sys
import os
from unittest.mock import patch

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

@pytest.fixture(autouse=True)
def mock_api_keys():
    """自动替换API密钥，避免真实API调用"""
    test_config = {
        'chatgpt': {
            'api_key': 'test-key',
            'base_url': 'https://test.api.com',
            'model': 'gpt-4',
            'embedding_model': 'text-embedding-3-small'
        },
        'chatglm': {
            'api_key': 'test-key',
            'model': 'glm-4.6',
            'embedding_model': 'embedding-3'
        }
    }
    with patch('app.llm.config.LLM_CONFIG', test_config):
        yield
