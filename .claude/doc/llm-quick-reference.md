# LLM接口快速参考

## 快速开始

### ChatGPT

```python
from app.llm.chatgpt import ChatGPTLLM
from app.llm.config import get_config

# 使用配置
config = get_config('chatgpt')
llm = ChatGPTLLM(**config)

# 发送消息
response = llm.send_message("你好，请介绍一下自己")
print(response)

# 获取嵌入向量
texts = ["示例文本"]
embeddings = llm.send_embedding(texts)
print(f"向量维度: {len(embeddings[0])}")  # 1536
```

### ChatGLM

```python
from app.llm.chatglm import ChatGLMLLM
from app.llm.config import get_config

# 使用配置
config = get_config('chatglm')
llm = ChatGLMLLM(**config)

# 发送消息（支持深度思考）
response = llm.send_message("请分析这个问题的逻辑")
print(response)

# 获取嵌入向量
texts = ["中文文本示例"]
embeddings = llm.send_embedding(texts)
print(f"向量维度: {len(embeddings[0])}")  # 1024
```

## 核心API

### send_message()

```python
# 基础用法
response = llm.send_message("提示文本")

# JSON格式响应
json_response = llm.send_message("返回JSON格式数据", json_flag=True)
```

### send_embedding()

```python
# 单个文本
embedding = llm.send_embedding(["文本"])

# 批量处理
embeddings = llm.send_embedding(["文本1", "文本2", "文本3"])
```

### get_lang_embedding()

```python
import chromadb

# ChromaDB集成
embedding_fn = llm.get_lang_embedding()
collection = client.create_collection(
    name="docs",
    embedding_function=embedding_fn
)
```

## 初始化参数

### ChatGPTLLM

| 参数 | 默认值 | 说明 |
|------|--------|------|
| api_key | 必需 | OpenAI API密钥 |
| base_url | None | API基础URL |
| model | "gpt-4" | 对话模型 |
| embedding_model | "text-embedding-3-small" | 嵌入模型 |
| temperature | 0.7 | 创造性控制 |
| max_tokens | 2048 | 最大token数 |

### ChatGLMLLM

| 参数 | 默认值 | 说明 |
|------|--------|------|
| api_key | 必需 | 智谱AI API密钥 |
| model | "glm-4.6" | 对话模型（支持深度思考） |
| embedding_model | "embedding-3" | 嵌入模型 |
| temperature | 1.0 | 创造性控制 |
| max_tokens | 65536 | 最大token数 |

## 配置示例

```python
# app/llm/config.py
LLM_CONFIG = {
    'chatgpt': {
        'api_key': 'sk-your-openai-key',
        'base_url': 'https://api.openai.com/v1',
        'model': 'gpt-4',
        'embedding_model': 'text-embedding-3-small'
    },
    'chatglm': {
        'api_key': 'your-zhipu-key',
        'model': 'glm-4.6',
        'embedding_model': 'embedding-3'
    }
}
```

## 运行测试

```bash
# 安装依赖
pdm install

# 运行所有测试
pdm run test

# 运行特定测试
pdm run test-chatgpt
pdm run test-chatglm
```

## ChromaDB集成

```python
import chromadb
from app.llm.config import get_config

# 初始化
config = get_config('chatgpt')
llm = ChatGPTLLM(**config)

# 创建集合
client = chromadb.Client()
collection = client.create_collection(
    name="documents",
    embedding_function=llm.get_lang_embedding()
)

# 添加文档
collection.add(
    documents=["文档内容1", "文档内容2"],
    ids=["doc1", "doc2"]
)

# 查询
results = collection.query(
    query_texts=["查询关键词"],
    n_results=2
)
```

## 错误处理

```python
response = llm.send_message("提示文本")
if response is None:
    print("API调用失败")
else:
    print(f"响应: {response}")

# 嵌入错误处理
embeddings = llm.send_embedding(["文本"])
if embeddings is None:
    print("嵌入生成失败")
else:
    print(f"生成 {len(embeddings)} 个向量")
```

## 性能提示

- ✅ 使用批量处理进行文本嵌入
- ✅ 合理设置temperature参数
- ✅ 选择适合任务大小的模型
- ✅ 利用内置重试机制
- ⚠️ 避免频繁的小批量API调用