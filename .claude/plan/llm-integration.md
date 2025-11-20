# LLM大模型接入模块开发计划

## 1. 项目概述

### 1.1 开发目标
为Casevo框架开发ChatGPT和ChatGLM的大语言模型接入模块，继承自 `src/casevo/llm_interface.py` 基类，在 `app/llm/` 目录下实现统一的对话和嵌入功能接口。

### 1.2 技术背景
- **基类**: [`src/casevo/llm_interface.py`](src/casevo/llm_interface.py) - 定义抽象接口
- **参考实现**: [`.claude/example/baichuan.py`](.claude/example/baichuan.py) - 百川接口实现
- **目标模型**: ChatGPT (OpenAI) 和 ChatGLM (智谱AI)
- **依赖**: `zai-sdk>=0.0.4.2` (智谱AI SDK) 和 `openai` 库
- **设计原则**: 保持 `src/casevo/` 目录完整性不变，新模块放在 `app/llm/` 目录

## 2. 接口分析

### 2.1 LLM_INTERFACE基类要求
```python
class LLM_INTERFACE(metaclass=ABCMeta):
    @abstractmethod
    def send_message(self, prompt, json_flag=False):
        """发送prompt，返回文本响应"""
        pass

    @abstractmethod
    def send_embedding(self, text_list):
        """发送文本列表，返回嵌入向量"""
        pass

    @abstractmethod
    def get_lang_embedding(self):
        """返回LangChain兼容的嵌入函数"""
        pass
```

### 2.2 百川实现分析
- **发送消息**: 使用HTTP POST请求到对话API
- **嵌入功能**: 使用ChromaDB的EmbeddingFunction
- **错误处理**: 处理429限流和content_filter
- **配置**: 支持temperature、top_p、max_tokens等参数

## 3. 目标模型接入方式

### 3.1 ChatGPT接入分析
**参考代码**: [`.claude/example/chatgpt.py`](.claude/example/chatgpt.py)

**关键信息**:
- 使用 `openai` 库
- 支持自定义base_url (如UniAPI代理)
- API Key通过环境变量获取
- 标准OpenAI API格式

**关键信息**:
- 使用 `openai` 库
- 支持自定义base_url (如UniAPI代理)
- API Key通过环境变量获取
- 标准OpenAI API格式
- 嵌入模型: text-embedding-3-small

**技术要点**:
- 对话API: chat.completions.create()
- 嵌入API: embeddings.create()
- 错误处理和重试机制
- 参数配置范围

### 3.2 ChatGLM接入分析
**参考代码**:
- [`.claude/example/chatglm.py`](.claude/example/chatglm.py) - 对话示例
- [`.claude/example/chatglm_embedding.py`](.claude/example/chatglm_embedding.py) - 嵌入示例

**关键信息**:
- 使用 `zai` SDK (ZhipuAiClient)
- 支持深度思考模式 (thinking参数)
- 对话模型: glm-4.6
- 嵌入模型: embedding-3
- 最大输出: 65536 tokens

**技术要点**:
- 对话API: client.chat.completions.create()
- 嵌入API: client.embeddings.create()
- 批量文本嵌入支持
- API调用格式和错误处理

## 4. 开发计划

### 4.1 第一阶段：环境准备和目录创建
- [ ] 创建 `app/llm/` 目录结构
- [ ] 安装依赖：`pdm add openai`
- [ ] 配置环境变量管理
- [ ] 创建配置文件模板

### 4.2 第二阶段：ChatGPT模块实现
- [ ] 实现 `app/llm/chatgpt.py` 中的 `ChatGPTLLM` 类
  - [ ] 继承 `src/casevo/llm_interface.LLM_INTERFACE`
  - [ ] 实现 `send_message()` 方法
  - [ ] 实现 `send_embedding()` 方法 (text-embedding-3-small)
  - [ ] 实现 `get_lang_embedding()` 方法
- [ ] 添加错误处理和重试机制
- [ ] 编写基础单元测试

### 4.3 第三阶段：ChatGLM模块实现
- [ ] 实现 `app/llm/chatglm.py` 中的 `ChatGLMLLM` 类
  - [ ] 继承 `src/casevo/llm_interface.LLM_INTERFACE`
  - [ ] 实现 `send_message()` 方法
  - [ ] 实现 `send_embedding()` 方法 (embedding-3)
  - [ ] 实现 `get_lang_embedding()` 方法
- [ ] 支持深度思考模式
- [ ] 编写基础单元测试

### 4.4 第四阶段：集成和文档
- [ ] 完善 `app/llm/config.py` 配置管理
- [ ] 创建使用示例和文档
- [ ] 性能测试和优化
- [ ] 代码质量检查

## 5. 技术实现细节

### 5.1 目录结构
```
app/llm/
├── __init__.py
├── chatgpt.py               # ChatGPT实现类
├── chatglm.py               # ChatGLM实现类
└── config.py                # 配置管理

# 保持 src/casevo/ 目录不变
src/casevo/
├── llm_interface.py         # 基类 (保持不变)
└── ... (其他现有模块)
```

### 5.2 配置管理
```python
# app/llm/config.py
import os

LLM_CONFIG = {
    'chatgpt': {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        'model': 'gpt-4',
        'embedding_model': 'text-embedding-3-small',
        'temperature': 0.7,
        'max_tokens': 2048
    },
    'chatglm': {
        'api_key': os.getenv('CHATGLM_API_KEY'),
        'model': 'glm-4.6',
        'embedding_model': 'embedding-3',
        'temperature': 1.0,
        'max_tokens': 65536
    }
}
```

### 5.3 实现示例
```python
# app/llm/chatgpt.py
from src.casevo.llm_interface import LLM_INTERFACE
from chromadb import Documents, EmbeddingFunction, Embeddings
from openai import OpenAI
import time

class ChatGPTLLM(LLM_INTERFACE):
    def __init__(self, api_key, base_url=None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def send_message(self, prompt, json_flag=False):
        # 实现对话逻辑
        pass

    def send_embedding(self, text_list):
        # 实现嵌入逻辑
        pass

    def get_lang_embedding(self):
        # 返回ChromaDB兼容的嵌入函数
        pass
```

### 5.4 错误处理策略
- **API限流**: 指数退避重试机制
- **网络错误**: 超时重试和异常捕获
- **认证错误**: 配置验证和提示

### 5.5 性能优化
- **批量嵌入**: 分批处理大量文本
- **缓存机制**: 缓存常用嵌入结果

## 6. 风险评估与解决方案

### 6.1 主要风险
- **API调用限制**: 实现分批处理和缓存机制
- **依赖版本问题**: zai-sdk和openai库版本兼容性
- **配置管理**: API密钥安全存储

### 6.2 解决方案
- 使用环境变量管理敏感配置
- 实现基础的重试和错误处理
- 保持实现简洁，避免过度复杂化

## 7. 开发里程碑

### 第1周: 基础搭建
- ✅ 创建 `app/llm/` 目录
- ✅ 配置文件和依赖安装
- ✅ ChatGPT类基本框架

### 第2周: 核心功能
- ✅ ChatGPT方法实现
- ✅ ChatGLM方法实现
- ✅ 基础测试验证

### 第3周: 优化完善
- ✅ 错误处理优化
- ✅ 性能调优
- ✅ 文档和示例

## 8. 使用示例

```python
# 使用ChatGPT
from app.llm.chatgpt import ChatGPTLLM
from app.llm.config import LLM_CONFIG

chatgpt = ChatGPTLLM(
    api_key=LLM_CONFIG['chatgpt']['api_key'],
    base_url=LLM_CONFIG['chatgpt']['base_url']
)

response = chatgpt.send_message("你好，请介绍一下狼人杀游戏")

# 使用ChatGLM
from app.llm.chatglm import ChatGLMLLM

chatglm = ChatGLMLLM(api_key=LLM_CONFIG['chatglm']['api_key'])
response = chatglm.send_message("你好，请介绍一下狼人杀游戏")
```