# LLM接口使用指南

## 概述

Casevo框架提供了两个主要的LLM（大语言模型）接口实现：ChatGPT和ChatGLM。这两个实现都继承自抽象基类`LLM_INTERFACE`，提供统一的标准接口。

## 基础架构

### 抽象基类：LLM_INTERFACE

所有LLM实现都必须继承自`LLM_INTERFACE`，并实现以下三个抽象方法：

```python
from abc import abstractmethod, ABCMeta

class LLM_INTERFACE(metaclass=ABCMeta):
    @abstractmethod
    def send_message(self, prompt, json_flag=False):
        """发送消息到LLM"""
        pass

    @abstractmethod
    def send_embedding(self, text_list):
        """获取文本嵌入向量"""
        pass

    @abstractmethod
    def get_lang_embedding(self):
        """获取ChromaDB兼容的嵌入函数"""
        pass
```

## ChatGPT接口

### 类：ChatGPTLLM

基于OpenAI API的ChatGPT实现。

#### 初始化参数

```python
def __init__(self, api_key: str, base_url: Optional[str] = None,
             model: str = "gpt-4", embedding_model: str = "text-embedding-3-small",
             temperature: float = 0.7, max_tokens: int = 2048):
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | str | 必需 | OpenAI API密钥 |
| `base_url` | Optional[str] | None | API基础URL（支持代理） |
| `model` | str | "gpt-4" | 对话模型名称 |
| `embedding_model` | str | "text-embedding-3-small" | 嵌入模型名称 |
| `temperature` | float | 0.7 | 温度参数（0-2，控制创造性） |
| `max_tokens` | int | 2048 | 最大生成token数 |

#### 核心方法

##### send_message()

```python
def send_message(self, prompt: str, json_flag: bool = False) -> Optional[str]:
```

**功能**：发送消息到ChatGPT并获取响应

**参数**：
- `prompt` (str): 输入的提示文本
- `json_flag` (bool): 是否要求返回JSON格式响应，默认为False

**返回值**：
- `Optional[str]`: 成功时返回响应文本，失败时返回None

**特性**：
- 支持JSON格式响应（用于结构化输出）
- 自动重试机制（限流时等待5秒）
- 错误处理和日志记录

**使用示例**：
```python
from app.llm.chatgpt import ChatGPTLLM

# 初始化
llm = ChatGPTLLM(
    api_key="your-api-key",
    model="gpt-4",
    temperature=0.7
)

# 普通对话
response = llm.send_message("请解释量子计算的基本原理")
print(response)

# JSON格式响应
json_response = llm.send_message("请以JSON格式返回用户信息", json_flag=True)
print(json_response)
```

##### send_embedding()

```python
def send_embedding(self, text_list: List[str]) -> Optional[List[List[float]]]:
```

**功能**：获取文本的嵌入向量

**参数**：
- `text_list` (List[str]): 待处理的文本列表

**返回值**：
- `Optional[List[List[float]]]`: 成功时返回向量列表，失败时返回None

**特性**：
- 自动批处理（每批100个文本）
- 防限流延迟（批间0.1秒间隔）
- 支持大批量文本处理

**使用示例**：
```python
# 单个文本嵌入
texts = ["这是一个测试文本"]
embeddings = llm.send_embedding(texts)
print(f"向量维度: {len(embeddings[0])}")  # 1536维

# 批量文本嵌入
texts = [
    "人工智能是未来的发展方向",
    "机器学习需要大量数据",
    "深度学习是机器学习的子集"
]
embeddings = llm.send_embedding(texts)
print(f"生成了 {len(embeddings)} 个向量")
```

##### get_lang_embedding()

```python
def get_lang_embedding(self) -> ChatGPTEmbedding:
```

**功能**：获取ChromaDB兼容的嵌入函数

**返回值**：
- `ChatGPTEmbedding`: ChromaDB嵌入函数实例

**使用示例**：
```python
import chromadb

# 获取嵌入函数
embedding_fn = llm.get_lang_embedding()

# 与ChromaDB集成
client = chromadb.Client()
collection = client.create_collection(
    name="documents",
    embedding_function=embedding_fn
)

# 添加文档
collection.add(
    documents=["示例文档内容"],
    ids=["doc1"]
)
```

### 辅助类：ChatGPTEmbedding

ChromaDB兼容的嵌入函数包装器。

#### 特性
- 继承自`chromadb.EmbeddingFunction`
- 支持批量处理
- 自动批大小管理（默认100）

#### 使用场景
- ChromaDB向量数据库集成
- 文档检索和相似性搜索

## ChatGLM接口

### 类：ChatGLMLLM

基于智谱AI API的ChatGLM实现。

#### 初始化参数

```python
def __init__(self, api_key: str, model: str = "glm-4.6",
             embedding_model: str = "embedding-3",
             temperature: float = 1.0, max_tokens: int = 65536):
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | str | 必需 | 智谱AI API密钥 |
| `model` | str | "glm-4.6" | 对话模型名称 |
| `embedding_model` | str | "embedding-3" | 嵌入模型名称 |
| `temperature` | float | 1.0 | 温度参数 |
| `max_tokens` | int | 65536 | 最大生成token数 |

**依赖要求**：
```bash
pip install zai-sdk
```

#### 核心方法

##### send_message()

```python
def send_message(self, prompt: str, json_flag: bool = False) -> Optional[str]:
```

**功能**：发送消息到ChatGLM并获取响应

**参数**：
- `prompt` (str): 输入的提示文本
- `json_flag` (bool): 是否要求返回JSON格式响应

**返回值**：
- `Optional[str]`: 成功时返回响应文本，失败时返回None

**特性**：
- **深度思考模式**：glm-4.6模型自动启用深度思考
- 支持JSON格式响应
- 自动重试机制
- 更高的token限制（65536）

**使用示例**：
```python
from app.llm.chatglm import ChatGLMLLM

# 初始化
llm = ChatGLMLLM(
    api_key="your-zhipu-api-key",
    model="glm-4.6"  # 支持深度思考
)

# 普通对话
response = llm.send_message("请分析这个商业案例的优势和劣势")
print(response)

# JSON格式响应
json_response = llm.send_message(
    "分析以下数据并返回JSON格式的报告：[数据]",
    json_flag=True
)
```

##### send_embedding()

```python
def send_embedding(self, text_list: List[str]) -> Optional[List[List[float]]]:
```

**功能**：获取文本的嵌入向量

**参数**：
- `text_list` (List[str]): 待处理的文本列表

**返回值**：
- `Optional[List[List[float]]]`: 成功时返回向量列表，失败时返回None

**特性**：
- 批量处理支持
- 1024维向量（embedding-3模型）
- 防限流机制

**使用示例**：
```python
# 文本嵌入
texts = ["这是一个中文文本示例"]
embeddings = llm.send_embedding(texts)
print(f"向量维度: {len(embeddings[0])}")  # 1024维

# 批量处理
documents = [
    "自然语言处理是AI的重要分支",
    "大语言模型改变了人机交互方式",
    "向量数据库支持语义搜索"
]
embeddings = llm.send_embedding(documents)
```

### 辅助类：ChatGLMEmbedding

ChromaDB兼容的嵌入函数。

#### 特性
- 专为中国语言优化
- 1024维嵌入向量
- 批量处理支持

## 配置管理

### 使用config.py统一配置

框架提供了统一的配置管理：

```python
from app.llm.config import get_config

# 获取ChatGPT配置
chatgpt_config = get_config('chatgpt')
llm = ChatGPTLLM(**chatgpt_config)

# 获取ChatGLM配置
chatglm_config = get_config('chatglm')
llm = ChatGLMLLM(**chatglm_config)
```

### 配置示例

```python
# app/llm/config.py
LLM_CONFIG = {
    'chatgpt': {
        'api_key': "your-openai-key",
        'base_url': "https://api.openai.com/v1",
        'model': 'gpt-4',
        'embedding_model': 'text-embedding-3-small',
        'temperature': 0.7,
        'max_tokens': 2048
    },
    'chatglm': {
        'api_key': "your-zhipu-key",
        'model': 'glm-4.6',
        'embedding_model': 'embedding-3',
        'temperature': 1.0,
        'max_tokens': 65536
    }
}
```

## 最佳实践

### 1. 错误处理

```python
response = llm.send_message("你好")
if response is None:
    print("API调用失败")
else:
    print(f"响应: {response}")
```

### 2. 批量嵌入优化

```python
# 推荐：批量处理
texts = ["文本1", "文本2", "文本3"]
embeddings = llm.send_embedding(texts)

# 避免：逐个处理（效率低）
for text in texts:
    embedding = llm.send_embedding([text])
```

### 3. ChromaDB集成

```python
import chromadb
from app.llm.config import get_config

# 初始化LLM
config = get_config('chatgpt')
llm = ChatGPTLLM(**config)

# 创建向量数据库
client = chromadb.Client()
collection = client.create_collection(
    name="documents",
    embedding_function=llm.get_lang_embedding()
)

# 添加文档
documents = [
    "机器学习是人工智能的子领域",
    "深度学习使用神经网络进行学习"
]

collection.add(
    documents=documents,
    ids=["doc1", "doc2"],
    metadatas=[{"source": "textbook"}, {"source": "paper"}]
)

# 查询
results = collection.query(
    query_texts=["什么是机器学习？"],
    n_results=2
)
```

### 4. 性能优化

- **批量处理**：文本嵌入时使用批量处理减少API调用
- **重试机制**：框架内置重试机制，处理限流错误
- **温度调节**：根据任务需求调整temperature参数

### 5. 模型选择建议

| 任务类型 | ChatGPT推荐 | ChatGLM推荐 |
|----------|-------------|-------------|
| 英文内容 | GPT-4 | - |
| 中文内容 | GPT-4 | GLM-4.6 |
| 代码生成 | GPT-4 | GLM-4.6 |
| 逻辑推理 | GPT-4 | GLM-4.6（深度思考） |
| 长文本处理 | GPT-4 Turbo | GLM-4.6（65536 tokens） |

## 测试

项目包含完整的测试套件：

```bash
# 运行所有测试
pdm run test

# 运行特定模块测试
pdm run test-chatgpt
pdm run test-chatglm
pdm run test-config
```

测试覆盖：
- 初始化测试
- 消息发送测试
- 文本嵌入测试
- 配置集成测试

## 常见问题

### Q: 如何处理API限流？
A: 框架内置重试机制，遇到限流会自动等待5秒后重试。

### Q: 如何选择合适的模型？
A: 参考上方的模型选择建议表，根据语言和任务类型选择。

### Q: 嵌入向量维度是多少？
A: ChatGPT: 1536维，ChatGLM: 1024维。

### Q: 支持哪些嵌入模型？
A: ChatGPT支持text-embedding-3-small/large，ChatGLM支持embedding-3。

### Q: 如何获取API密钥？
A: ChatGPT: https://platform.openai.com/api-keys，ChatGLM: https://open.bigmodel.cn/

## 版本兼容性

- **Python**: >=3.11
- **OpenAI**: >=2.7.2
- **zai-sdk**: >=0.0.4.2
- **chromadb**: >=0.5.0