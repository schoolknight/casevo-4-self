# Casevo LLM 接入示例

本目录包含 OpenAI 和智谱 GLM 的接入示例代码。

## 快速开始

### 1. 安装依赖

```bash
# OpenAI
pip install "casevo[openai]"

# 智谱 GLM
pip install "casevo[glm]"

# 或者同时安装
pip install "casevo[openai,glm]"
```

### 2. 配置 API Key

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
```

### 3. 运行示例

```bash
# OpenAI 示例
python examples/openai_example.py

# GLM 示例
python examples/glm_example.py
```

## 文件说明

| 文件 | 说明 |
|---|---|
| `.env.example` | 环境变量模板 |
| `openai_example.py` | OpenAI 接入示例 |
| `glm_example.py` | 智谱 GLM 接入示例 |

## 安全提示

- `.env` 文件已添加到 `.gitignore`，不会被提交到 Git
- 请勿将 API Key 硬编码到代码中
- 定期轮换你的 API Key
