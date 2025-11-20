# ChatGPT和ChatGLM简化测试计划

## 1. 测试目标

为ChatGPT和ChatGLM模块创建简洁的pytest单元测试，确保核心功能正常工作。

## 2. 测试范围

- `app/llm/chatgpt.py` - ChatGPT LLM实现
- `app/llm/chatglm.py` - ChatGLM LLM实现
- `app/llm/config.py` - 配置管理模块

## 3. 目录结构
```
tests/
├── __init__.py
├── conftest.py          # 配置和fixtures
├── test_chatgpt.py      # ChatGPT测试
├── test_chatglm.py      # ChatGLM测试
└── test_config.py       # 配置测试
```

## 4. 核心测试用例

### 4.1 ChatGPT测试 (test_chatgpt.py)
```python
import pytest
from unittest.mock import patch
from app.llm.chatgpt import ChatGPTLLM

def test_chatgpt_initialization():
    """测试ChatGPT初始化"""
    pass

@patch('openai.OpenAI')
def test_chatgpt_send_message(mock_openai):
    """测试消息发送"""
    pass

@patch('openai.OpenAI')
def test_chatgpt_send_embedding(mock_openai):
    """测试文本嵌入"""
    pass
```

### 4.2 ChatGLM测试 (test_chatglm.py)
```python
import pytest
from unittest.mock import patch
from app.llm.chatglm import ChatGLMLLM

def test_chatglm_initialization():
    """测试ChatGLM初始化"""
    pass

@patch('zai.ZhipuAI')
def test_chatglm_send_message(mock_zhipu):
    """测试消息发送"""
    pass

@patch('zai.ZhipuAI')
def test_chatglm_send_embedding(mock_zhipu):
    """测试文本嵌入"""
    pass
```

### 4.3 配置测试 (test_config.py)
```python
import pytest
from llm.config import get_config, validate_config

def test_get_config():
    """测试配置获取"""
    assert get_config('chatgpt')['model'] == 'gpt-4'
    assert get_config('chatglm')['model'] == 'glm-4.6'

def test_validate_config():
    """测试配置验证"""
    assert validate_config('chatgpt') == True
    assert validate_config('chatglm') == True
    assert validate_config('invalid') == False
```

## 5. 配置文件 (conftest.py)
```python
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
    with patch('llm.config.LLM_CONFIG') as mock_config:
        mock_config.return_value = {
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
        yield
```

## 6. 项目配置

### 6.1 依赖安装
```bash
pdm add pytest pytest-mock
```

### 6.2 pyproject.toml配置
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.pdm.scripts]
test = "pytest tests/ -v"
test-chatgpt = "pytest tests/test_chatgpt.py -v"
test-chatglm = "pytest tests/test_chatglm.py -v"
```

## 7. 运行命令
```bash
# 运行所有测试
pdm run test

# 运行特定模块
pdm run test-chatgpt
pdm run test-chatglm

# 详细输出
pytest tests/ -v
```

## 8. 实施步骤

1. **创建目录结构**
   ```bash
   mkdir -p tests
   touch tests/__init__.py tests/conftest.py
   ```

2. **创建测试文件**
   ```bash
   touch tests/test_chatgpt.py tests/test_chatglm.py tests/test_config.py
   ```

3. **编写测试代码**
   - 每个模块3个核心测试
   - 使用config.py的配置结构
   - Mock避免真实API调用

4. **运行验证**
   ```bash
   pdm run test
   ```

## 9. 维护要点

- 配置变更时同步更新测试
- 保持测试简洁，每个文件<50行
- 运行时间控制在1分钟内
- Mock响应数据与真实API一致