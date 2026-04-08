# Casevo LLM 示例

本目录提供 OpenAI 与 GLM（智谱）接入示例，演示如何通过 `.env` 安全加载 API Key 并调用 Casevo 的 LLM 适配层。

## 快速开始

1. 安装依赖（包含示例依赖组）

```bash
pdm install -G openai -G glm -G example
```

2. 配置环境变量

```bash
cp examples/.env.example examples/.env
```

然后编辑 `examples/.env`，填入真实 API Key。

3. 运行示例

```bash
pdm run python examples/openai_example.py
pdm run python examples/glm_example.py
```

## 示例说明

- `openai_example.py`
  - 使用 `OpenAI_LLM` 初始化客户端（支持 `OPENAI_BASE_URL`、`OPENAI_MODEL`）。
  - 展示 `send_message` 基础对话。
  - 展示 `send_message_by_config`（使用 `LLMConfig` 控制参数）。
  - 展示 `send_embedding` 批量向量化。

- `glm_example.py`
  - 使用 `GLM_LLM` 初始化客户端（默认智谱 OpenAI 兼容端点）。
  - 展示 `send_message` 基础对话。
  - 展示 `send_message_by_config`（使用 `LLMConfig` 控制参数）。
  - 展示 `send_embedding` 批量向量化。

## 注意事项

- 请勿在代码中硬编码 API Key，统一通过 `.env` 或系统环境变量注入。
- `examples/.env` 不应提交到仓库（项目 `.gitignore` 已包含 `.env`）。
- 若调用失败，请先检查网络连通性、密钥权限和模型名称是否可用。
