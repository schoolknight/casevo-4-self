# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**Casevo (Cognitive agents and social evolution simulator)** 是一个基于复杂网络构建社会模拟多智能体实验或应用的Python框架。该项目基于Mesa框架开发，专注于认知智能体和社会演化模拟。

### 当前开发目标：智能体狼人杀模拟器
基于Casevo框架开发一个智能体狼人杀模拟器，让每个AI智能体扮演游戏中的特定角色，通过语言逻辑推理进行社交推理游戏。

**游戏特点：**
- **角色扮演**: 智能体扮演狼人、预言家、女巫、猎人、守卫、平民等角色
- **逻辑推理**: 基于有限信息进行身份推断和策略制定
- **语言交互**: 通过自然语言发言、辩论和投票
- **阵营对抗**: 狼人阵营vs好人阵营的博弈对抗

### 核心依赖
- **Python**: >=3.11
- **Mesa**: ==2.4.0 (ABM智能体建模工具)
- **ChromaDB**: >=0.5.0 (向量数据库，用于记忆机制)
- **OpenAI**: >=2.7.2 (ChatGPT API支持)
- **zai-sdk**: >=0.0.4.2 (智谱AI ChatGLM支持)
- **pytest**: >=7.0.0 (测试框架)

## 开发环境设置

### 包管理
项目使用 **PDM** 作为包管理工具：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pdm install

# 构建项目
pdm build
```

### 运行环境
- Python解释器位于：`.venv/bin/python`
- 项目使用PDM管理的虚拟环境

## 项目架构

### 核心模块结构 (`src/casevo/`)

**基础框架模块：**
- [`agent_base.py`](src/casevo/agent_base.py) - 智能体基类，继承自Mesa的Agent
- [`model_base.py`](src/casevo/model_base.py) - 模型基类，继承自Mesa的Model
- [`base_component.py`](src/casevo/base_component.py) - 组件基类

**思维链与交互：**
- [`chain.py`](src/casevo/chain.py) - 思维链系统，支持BaseStep、ChoiceStep、ScoreStep、JsonStep
- [`prompt.py`](src/casevo/prompt.py) - 提示词模板系统，集成Jinja2模板引擎
- [`llm_interface.py`](src/casevo/llm_interface.py) - 大语言模型接口抽象类

**记忆与知识管理：**
- [`memory.py`](src/casevo/memory.py) - 记忆机制系统，支持短期/长期记忆和RAG
- [`background.py`](src/casevo/background.py) - 外部知识库RAG功能

**工具模块 (`util/`)**：
- [`tot_log.py`](src/casevo/util/tot_log.py) - 日志记录系统
- [`tot_log_stream.py`](src/casevo/util/tot_log_stream.py) - 流式日志系统 (0.3.19新增)
- [`thread_send.py`](src/casevo/util/thread_send.py) - 线程发送工具
- [`cache.py`](src/casevo/util/cache.py) - 缓存系统

**LLM接口模块 (`app/llm/`)**：
- [`chatgpt.py`](app/llm/chatgpt.py) - ChatGPT LLM实现，支持对话和嵌入
- [`chatglm.py`](app/llm/chatglm.py) - ChatGLM LLM实现，支持深度思考模式
- [`config.py`](app/llm/config.py) - LLM配置管理模块
- [`__init__.py`](app/llm/__init__.py) - 模块初始化和导出

**测试模块 (`tests/`)**：
- [`test_chatgpt.py`](tests/test_chatgpt.py) - ChatGPT模块单元测试
- [`test_chatglm.py`](tests/test_chatglm.py) - ChatGLM模块单元测试
- [`test_config.py`](tests/test_config.py) - 配置模块测试
- [`conftest.py`](tests/conftest.py) - pytest配置和Mock设置

### 设计模式与架构原则

**工厂模式应用：**
- `PromptFactory` - 统一管理提示词模板
- `MemoryFactory` - 全局记忆管理工厂
- `BackgroundFactory` - 外部知识库工厂

**组件化设计：**
- 所有核心组件继承自相应的基类
- 支持插件式扩展和自定义实现

**思维链模式：**
- 支持多步骤推理过程
- 可自定义步骤类型（基础步骤、选择步骤、评分步骤、JSON步骤）

## 常用开发命令

### 环境管理
```bash
# 激活虚拟环境
source .venv/bin/activate

# 查看已安装的Python包
pip list

# 安装新的依赖
pdm add <package_name>
```

### 项目构建
```bash
# 构建项目
pdm build

# 构建wheel包
pyproject-build
```

### 运行示例

**选举模拟示例（参考实现）：**
```bash
# 运行选举模拟示例
python run.py case_lite.json 6
```

**狼人杀模拟器开发中：**
- 详细需求文档：[`.claude/plan/req.md`](.claude/plan/req.md)
- 开发计划：分阶段实现基础框架、角色技能和优化完善
- 目标配置：支持6-12人游戏，可配置角色和规则

## 关键开发概念

### 智能体 (Agent) 开发
- 继承 `AgentBase` 类
- 实现思维链设置：`setup_chain(chain_dict)`
- 必须实现 `step()` 方法定义智能体行为
- 使用记忆系统进行状态管理

**狼人杀智能体特点：**
- **角色特化**: 每个智能体有特定的角色技能和策略
- **信息推理**: 基于夜间信息和白天发言进行逻辑推理
- **博弈策略**: 制定发言、投票和技能使用策略
- **团队协作**: 阵营内信息共享和协调配合

### 模型 (Model) 开发
- 继承 `ModelBase` 类
- 管理网络结构和调度器
- 通过 `add_agent()` 添加智能体
- 实现全局事件函数

**狼人杀模型特点：**
- **阶段管理**: 控制夜晚/白天阶段转换和行动顺序
- **规则执行**: 实现技能使用、投票、胜负判定等游戏规则
- **状态同步**: 确保所有智能体对游戏状态的一致认知
- **事件日志**: 记录游戏过程用于分析和复盘

### 大语言模型集成
- 继承 `LLM_INTERFACE` 抽象基类
- 实现必需方法：`send_message()`, `send_embedding()`, `get_lang_embedding()`
- **ChatGPT实现**: 支持OpenAI API，JSON格式响应，1536维嵌入向量
- **ChatGLM实现**: 支持智谱AI API，深度思考模式，1024维嵌入向量
- **配置管理**: 统一的配置系统，支持API密钥和模型参数管理

### LLM接口使用示例

```python
from app.llm.config import get_config
from app.llm.chatgpt import ChatGPTLLM
from app.llm.chatglm import ChatGLMLLM

# 使用配置系统
config = get_config('chatgpt')  # 或 'chatglm'
llm = ChatGPTLLM(**config)

# 发送消息
response = llm.send_message("你好，请介绍一下自己")

# 获取嵌入向量
embeddings = llm.send_embedding(["示例文本"])

# ChromaDB集成
embedding_fn = llm.get_lang_embedding()
```

### 提示词模板
- 使用Jinja2模板语法
- 通过 `PromptFactory` 统一管理
- 支持动态参数注入

### 测试系统
- **pytest框架**: 支持单元测试和集成测试
- **Mock策略**: 自动Mock API调用，避免真实API消耗
- **配置集成**: 测试使用真实配置结构，API密钥自动替换
- **运行命令**: `pdm run test` (全部), `pdm run test-chatgpt` (ChatGPT), `pdm run test-chatglm` (ChatGLM)

**狼人杀提示词特点：**
- **角色认知**: 明确智能体的身份、技能和胜利条件
- **信息处理**: 整合夜间行动信息和白天发言内容
- **策略制定**: 根据游戏阶段制定相应的发言和行动策略
- **逻辑推理**: 支持身份推断、谎言识别和逻辑分析

## 重要文件说明

**项目配置：**
- `pyproject.toml` - 项目配置和依赖管理
- `pdm.lock` - 锁定的依赖版本
- `README.md` - 详细的使用教程和API文档
- `logo_casevo.svg` - 项目Logo

**狼人杀开发相关：**
- [`.claude/plan/req.md`](.claude/plan/req.md) - 狼人杀模拟器详细需求文档
- [`.claude/target.md`](.claude/target.md) - 原始需求描述
- `.claude/plan/` - 开发计划目录

**LLM接口文档：**
- [`.claude/doc/README.md`](.claude/doc/README.md) - LLM接口文档索引和快速导航
- [`.claude/doc/llm-quick-reference.md`](.claude/doc/llm-quick-reference.md) - LLM接口快速参考指南
- [`.claude/doc/llm-interface-guide.md`](.claude/doc/llm-interface-guide.md) - LLM接口详细使用指南
- [`.claude/doc/llm-comparison.md`](.claude/doc/llm-comparison.md) - ChatGPT vs ChatGLM对比分析

**开发和测试相关：**
- [`.claude/plan/pytest-test-plan.md`](.claude/plan/pytest-test-plan.md) - 简化测试计划和实施方案
- `tests/` - 测试目录，包含LLM模块完整测试套件

## 注意事项

1. **Python版本要求**: 必须使用Python 3.11+
2. **日志目录**: 运行时需要清空log目录以避免日志累积
3. **记忆数据库**: 使用ChromaDB作为向量数据库存储记忆
4. **网络结构**: 支持NetworkX格式的复杂网络结构
5. **版本更新**: 0.3.19版本新增了TotLogStream和VariableNetwork功能
6. **API密钥管理**: 使用配置文件管理LLM API密钥，测试时自动Mock替换
7. **依赖安装**: ChatGLM需要安装`zai-sdk`，ChatGPT需要`openai`包
8. **测试隔离**: 测试框架自动Mock API调用，避免真实API消耗

## 狼人杀开发指南

### 开发重点
1. **角色智能体设计**: 每个角色需要独特的思维链和策略
2. **信息不对称管理**: 合理处理不同角色的信息获取和隐私
3. **逻辑推理能力**: 实现基于部分信息的身份推断
4. **自然语言交互**: 生成符合角色特点的发言内容

### 技术挑战
1. **复杂状态管理**: 游戏状态在夜晚和白天阶段的正确切换
2. **技能交互逻辑**: 多个技能同时使用的优先级和冲突处理
3. **智能体协作**: 阵营内智能体的信息共享和策略协调
4. **平衡性调优**: 确保不同角色和阵营的胜率平衡

### 开发资源
- 详细需求：[`.claude/plan/req.md`](.claude/plan/req.md)
- 参考实现：README.md中的选举模拟示例
- 框架文档：Casevo核心模块API说明
- **LLM接口文档**: [`.claude/doc/`](.claude/doc/) - 完整的LLM接口使用指南
- **测试参考**: [`tests/`](tests/) - LLM模块测试用例和最佳实践

## 学术引用

该项目已发表学术论文，如需使用请引用：
```
@misc{jiang2024casevocognitiveagentssocial,
      title={Casevo: A Cognitive Agents and Social Evolution Simulator},
      author={Zexun Jiang and Yafang Shi and Maoxu Li and Hongjiang Xiao and Yunxiao Qin and Qinglan Wei and Ye Wang and Yuan Zhang},
      year={2024},
      eprint={2412.19498},
      archivePrefix={arXiv},
      primaryClass={cs.SI},
      url={https://arxiv.org/abs/2412.19498},
}
```

## LLM接口扩展 (新增功能)

### 功能概述

项目已集成完整的LLM接口系统，支持ChatGPT和ChatGLM两种主流大语言模型，为智能体提供强大的自然语言处理和推理能力。

### 核心特性

**1. 统一接口设计**
- 基于`LLM_INTERFACE`抽象基类的统一API
- 支持消息发送、文本嵌入、ChromaDB集成
- 无缝切换不同LLM提供商

**2. 智能体集成**
- 智能体可直接使用LLM进行自然语言交互
- 支持复杂对话和逻辑推理
- 集成记忆系统和上下文管理

**3. 向量数据库支持**
- ChromaDB兼容的嵌入函数
- 支持语义搜索和相似性匹配
- 批量文本处理优化

### 在狼人杀项目中的应用

**角色扮演增强**
- 智能体可理解复杂角色设定和规则
- 生成符合角色特点的发言内容
- 支持策略性对话和心理博弈

**逻辑推理支持**
- 基于有限信息进行身份推断
- 分析发言模式和逻辑漏洞
- 制定投票和技能使用策略

**游戏状态分析**
- 实时分析游戏局势
- 评估各方阵营优势
- 生成游戏总结和分析报告

### 配置和使用

```python
# 在智能体中使用LLM
from app.llm.config import get_config
from app.llm.chatglm import ChatGLMLLM

class WerewolfAgent(AgentBase):
    def __init__(self, role="werewolf"):
        super().__init__()
        self.role = role

        # 初始化LLM
        config = get_config('chatglm')  # 使用中文优化模型
        self.llm = ChatGLMLLM(**config)

        # 设置角色提示词
        self.role_prompt = f"你是狼人杀游戏中的{role}，请以该角色身份发言。"

    def generate_statement(self, game_context):
        """生成发言内容"""
        prompt = self.role_prompt + f"\n当前游戏状况：{game_context}\n请你的发言："
        return self.llm.send_message(prompt)

    def analyze_suspects(self, statements):
        """分析可疑玩家"""
        analysis_prompt = f"分析以下发言，找出最可疑的玩家：{statements}"
        return self.llm.send_message(analysis_prompt)
```

### 测试和质量保证

**完整测试覆盖**
- 单元测试：初始化、消息发送、文本嵌入
- 集成测试：配置系统、ChromaDB集成
- Mock测试：API调用隔离，避免真实消耗

**性能优化**
- 批量处理减少API调用
- 自动重试机制处理限流
- 配置缓存和连接复用

### 文档支持

- 📚 [详细使用指南](.claude/doc/llm-interface-guide.md)
- 🚀 [快速参考](.claude/doc/llm-quick-reference.md)
- ⚖️ [模型对比分析](.claude/doc/llm-comparison.md)
- 🧪 [测试计划](.claude/plan/pytest-test-plan.md)