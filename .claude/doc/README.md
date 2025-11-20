# LLM接口文档

本文档目录包含Casevo框架中ChatGPT和ChatGLM接口的完整说明文档。

## 📚 文档结构

### 🚀 [快速参考](llm-quick-reference.md)
- 快速上手指南
- 核心API使用示例
- 常用代码模板
- 性能优化提示

### 📖 [详细使用指南](llm-interface-guide.md)
- 完整的API文档
- 参数详细说明
- 最佳实践指南
- ChromaDB集成教程
- 错误处理和调试
- 常见问题解答

### ⚖️ [接口对比分析](llm-comparison.md)
- ChatGPT vs ChatGLM详细对比
- 性能和成本分析
- 使用场景建议
- 迁移指南
- 混合使用策略

## 🎯 快速开始

### 1. 选择模型

```python
# ChatGPT（适合英文、代码生成）
from app.llm.chatgpt import ChatGPTLLM
llm = ChatGPTLLM(api_key="your-openai-key")

# ChatGLM（适合中文、深度思考）
from app.llm.chatglm import ChatGLMLLM
llm = ChatGLMLLM(api_key="your-zhipu-key")
```

### 2. 基础使用

```python
# 发送消息
response = llm.send_message("你好，请介绍一下自己")

# 获取嵌入向量
embeddings = llm.send_embedding(["示例文本"])

# ChromaDB集成
embedding_fn = llm.get_lang_embedding()
```

### 3. 配置管理

```python
from app.llm.config import get_config

# 使用统一配置
config = get_config('chatgpt')  # 或 'chatglm'
llm = ChatGPTLLM(**config)
```

## 🔧 环境要求

- **Python**: >=3.11
- **依赖包**:
  - `openai>=2.7.2` (ChatGPT)
  - `zai-sdk>=0.0.4.2` (ChatGLM)
  - `chromadb>=0.5.0` (向量数据库)

```bash
# 安装依赖
pdm install
```

## 🧪 运行测试

```bash
# 所有测试
pdm run test

# 特定模块测试
pdm run test-chatgpt
pdm run test-chatglm
pdm run test-config
```

## 📋 使用建议

| 场景 | 推荐模型 | 说明 |
|------|----------|------|
| 中文内容创作 | ChatGLM | 中文理解更准确 |
| 代码生成 | ChatGPT | 代码能力更强 |
| 英文写作 | ChatGPT | 英文表达更地道 |
| 逻辑推理 | ChatGLM | 深度思考模式 |
| 长文本处理 | ChatGLM | 支持65536 token |
| JSON输出 | ChatGPT | 原生支持 |

## 🆘 获取帮助

### API密钥申请
- **ChatGPT**: https://platform.openai.com/api-keys
- **ChatGLM**: https://open.bigmodel.cn/

### 相关链接
- [OpenAI API文档](https://platform.openai.com/docs)
- [智谱AI文档](https://open.bigmodel.cn/dev/api)
- [ChromaDB文档](https://docs.trychroma.com/)

### 问题反馈
如果在使用过程中遇到问题，请：
1. 检查[常见问题解答](llm-interface-guide.md#常见问题)
2. 查看测试用例了解正确用法
3. 运行测试确认环境配置

## 📝 文档更新

本文档会随着框架更新持续维护，最后更新时间：2025-11-20

---

**提示**：建议从[快速参考](llm-quick-reference.md)开始阅读，然后根据需要查看详细文档。