# LLM接入模块

本模块为Casevo框架提供了ChatGPT和ChatGLM的大语言模型接入功能。

## 文件结构

```
app/llm/
├── __init__.py       # 模块初始化和工厂函数
├── chatgpt.py        # ChatGPT实现类
├── chatglm.py        # ChatGLM实现类
├── config.py         # 配置管理
├── example.py        # 使用示例
└── README.md         # 说明文档
```

## 快速开始

### 1. 环境配置

设置环境变量：

```bash
# ChatGPT配置
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选

# ChatGLM配置
export CHATGLM_API_KEY="your-chatglm-api-key"
```

### 2. 基本使用

```python
# 方法1: 直接使用类
from app.llm import ChatGPTLLM, ChatGLMLLM

# ChatGPT
chatgpt = ChatGPTLLM(api_key="your-api-key")
response = chatgpt.send_message("你好")

# ChatGLM
chatglm = ChatGLMLLM(api_key="your-api-key")
response = chatglm.send_message("你好")

# 方法2: 使用工厂函数
from app.llm import create_llm

llm = create_llm('chatgpt')  # 或 'chatglm'
response = llm.send_message("你好")
```

### 3. 嵌入功能

```python
from app.llm import ChatGPTLLM

chatgpt = ChatGPTLLM(api_key="your-api-key")

# 获取嵌入向量
texts = ["文本1", "文本2", "文本3"]
embeddings = chatgpt.send_embedding(texts)

# ChromaDB兼容的嵌入函数
embedding_function = chatgpt.get_lang_embedding()
embeddings = embedding_function(texts)
```

## 功能特性

### ChatGPT支持
- 对话模型: gpt-4, gpt-3.5-turbo等
- 嵌入模型: text-embedding-3-small, text-embedding-3-large
- JSON格式响应支持
- 自定义base_url支持（兼容UniAPI等代理）

### ChatGLM支持
- 对话模型: glm-4.6, glm-4等
- 嵌入模型: embedding-3
- 深度思考模式支持
- 大规模token输出支持

### 通用功能
- 自动重试机制
- 批量嵌入处理
- ChromaDB集成
- 配置管理
- 错误处理

## 配置选项

### ChatGPT配置
```python
{
    'api_key': 'your-api-key',
    'base_url': 'https://api.openai.com/v1',  # 可选
    'model': 'gpt-4',
    'embedding_model': 'text-embedding-3-small',
    'temperature': 0.7,
    'max_tokens': 2048
}
```

### ChatGLM配置
```python
{
    'api_key': 'your-api-key',
    'model': 'glm-4.6',
    'embedding_model': 'embedding-3',
    'temperature': 1.0,
    'max_tokens': 65536
}
```

## 示例代码

运行完整示例：

```bash
cd app/llm
python example.py
```

示例包含：
- 基本对话功能
- 嵌入向量生成
- JSON格式响应
- 工厂函数使用
- ChromaDB集成

## 依赖要求

- openai>=1.0.0
- zai-sdk>=0.0.4.2
- chromadb>=0.5.0

## 注意事项

1. **API密钥安全**: 请使用环境变量存储API密钥，不要硬编码在代码中
2. **限流处理**: 模块内置了简单的重试机制，但仍需注意API调用频率限制
3. **嵌入批处理**: 大量文本建议分批处理，避免单次请求过大
4. **网络环境**: 中国大陆用户可能需要使用代理访问OpenAI API

## 错误处理

模块提供了完善的错误处理机制：

- API限流自动重试
- 网络错误恢复
- 配置验证
- 依赖检查

## 扩展开发

如需添加新的LLM提供商：

1. 继承 `src.casevo.llm_interface.LLM_INTERFACE`
2. 实现三个必需方法：`send_message`, `send_embedding`, `get_lang_embedding`
3. 在 `config.py` 中添加配置
4. 在 `__init__.py` 中导出新类

详细参考现有的 `ChatGPTLLM` 和 `ChatGLMLLM` 实现。