# Casevo 项目扫描快照（2026-04-05）

## 变更记录

| 时间 | 内容 |
|---|---|
| 2026-04-05 | 基于源码与测试结果重写根 `CLAUDE.md`，清理过时信息并补充当前工程事实。 |
| 2026-04-05 | 修复 `background.py` 的并发锁缺失与方法名调用错误，并新增对应单元测试。 |
| 2026-04-07 | 完成 R005：融合 `async_workflow` 的 LLM/Prompt 异步能力回顶层模块，补充兼容性测试。 |
| 2026-04-08 | 完成 R011：新增 `OpenAI_LLM` / `GLM_LLM` 实现、单元测试、依赖组与 README 快速接入文档。 |
| 2026-04-16 | 完成 R020：新增 `examples/async_workflow/` 示例（基础流程与流式流程）、示例文档与运行说明。 |
| 2026-08-30 | 完成 R021-1：新增 `FlovoClient` WebSocket 客户端、fake WS 单元测试与使用/异常说明。 |
| 2026-08-30 | 完成 R021-2：新增 Flovo `agent_dialog` 同步/流式示例、真实服务集成测试与运行文档。 |
| 2026-08-30 | 完成 R021-3：标记 `async_workflow` 已废弃，推荐使用 `FlovoClient`；保留原模块与导出以维持兼容性。 |
| 2026-08-31 | 完成 R023 Casevo 侧：`FlovoClient` 支持可选 `context`，补齐信封、兼容性、类型校验与真实链路测试，更新示例和文档；分支 `feature/R023-context-bridge`。 |
| 2026-08-31 | 完成 R024 Casevo 侧：升级 `agent_dialog` 真实 LLM/mock 降级示例，更新 context 个性化集成断言、运行文档与异常说明；分支 `feature/R024-real-llm-demo`。 |
| 2026-08-31 | 完成 R025+R006：为 `TotLogStream` 增加线程安全发布-订阅核心与 owner/type 过滤、异常隔离，并为 `init_log` 增加 `clear_old` 自动清理选项；分支 `feature/R025-log-stream`。 |
| 2026-09-01 | 完成 R026：新增 `LogStreamServer` WebSocket 推送适配器与本机集成测试；分支 `feature/R026-log-stream-server`。 |

## 项目定位

Casevo（Cognitive Agents and Social Evolution Simulator）是一个基于 Python 的多智能体社会模拟框架，核心能力包括：
- Mesa 驱动的 ABM 模型基座
- LLM 接口抽象
- ChromaDB 记忆检索与反思
- CoT（ThoughtChain）步骤编排
- `TotLogStream` 日志发布订阅与 `LogStreamServer` WebSocket 实时转发
- 异步工作流子系统（`src/casevo/async_workflow/`，已废弃并由 Flovo 引擎取代；保留用于兼容存量代码）

论文链接：<https://arxiv.org/abs/2412.19498>

## 当前工程结构（已扫描）

```text
.
├── pyproject.toml
├── README.md
├── src/casevo/
│   ├── __init__.py
│   ├── agent_base.py
│   ├── model_base.py
│   ├── chain.py
│   ├── prompt.py
│   ├── memory.py
│   ├── background.py
│   ├── llm_interface.py
│   ├── base_component.py
│   ├── async_workflow/
│   │   ├── workflow.py
│   │   ├── node.py
│   │   ├── para_bus.py
│   │   ├── prompt.py
│   │   ├── llm_interface.py
│   │   └── register_node.py
│   └── util/
│       ├── cache.py
│       ├── thread_send.py
│       ├── tot_log.py
│       ├── tot_log_stream.py
│       ├── log_stream_server.py
│       ├── log.py
│       └── random_name.py
└── tests/
    ├── test_llm_interface.py
    ├── test_background.py
    ├── test_chain.py
    ├── test_prompt.py
    ├── util/
    │   ├── test_cache.py
    │   └── test_random_name.py
    └── async_workflow/
        ├── test_llm_interface.py
        ├── test_para_bus.py
        ├── test_prompt.py
        └── test_workflow.py
```

## 依赖与环境

- Python: `>=3.11`
- 包管理: `pdm`
- 项目版本: `0.3.19`
- 核心依赖:
  - `mesa==2.4.0`
  - `chromadb>=0.5.0`
  - `requests>=2.33.1`
- 日志流网络适配使用环境中既有的 `websockets==16.0` 传递依赖，本任务不新增依赖。
- 测试依赖（optional group `test`）:
  - `pytest>=8,<9`
  - `pytest-cov>=5,<6`

## 对外 API（`src/casevo/__init__.py`）

已导出同步与异步两套接口，典型入口包括（异步工作流导出已废弃，仅为兼容保留）：
- 同步：`AgentBase`、`ModelBase`、`ThoughtChain`、`BaseStep`/`ChoiceStep`/`ScoreStep`/`JsonStep`、`PromptFactory`、`RequestCache`
- 异步：`AsyncWorkFlow`、`AsyncWorkflowManager`、`AsyncBaseNode`、`AsyncParameterBus`、`AsyncPromptFactory`、`async_register_class`

## 开发与验证命令

```bash
pdm install
pdm run pytest
```

## R005 融合记录（2026-04-07）

### 目标

将 `src/casevo/async_workflow/llm_interface.py` 与 `src/casevo/async_workflow/prompt.py` 的异步能力融合回顶层 `src/casevo/llm_interface.py` 与 `src/casevo/prompt.py`，并保持同步 API 向后兼容。

### 变更说明

1. `src/casevo/llm_interface.py`
   - 保留原有同步抽象方法签名：`send_message` / `send_embedding` / `get_lang_embedding`。
   - 在基类中新增异步工作流相关接口：
     - `chat`（默认优先 `send_message_by_config`，未实现时回退 `send_message`）
     - `chat_async` / `chat_stream` / `intent_analysis` / `intent_analysis_async`（默认抛 `NotImplementedError`）
   - `LLMConfig` 保留并确认包含 `temperature`/`max_tokens` 可选字段及 `to_dict()`。

2. `src/casevo/prompt.py`
   - 保留原有 `Prompt` 与 `PromptFactory.get_template()` 同步调用链。
   - 新增异步提示词抽象与实现：
     - `PromptBase` / `PromptChat` / `PromptChatStream` / `PromptIntentAnalysis`
   - `PromptFactory` 新增 `build_prompt(prompt_type, template_name, intents=None)`。
   - `PromptFactory.__send_message__` 扩展为同时支持：
     - 同步 `send_message(prompt_text)`
     - 异步 `chat` / `chat_stream` / `intent_analysis` 分发

3. `src/casevo/async_workflow/` 兼容策略
   - `async_workflow/prompt.py` 改为复用顶层 prompt 实现，保留原导入路径可用。
   - `async_workflow/llm_interface.py` 保留历史异步抽象契约，同时适配顶层同步接口（提供 `send_message`/`send_message_by_config` 默认桥接）。

4. 测试新增
   - `tests/test_llm_interface.py`：覆盖 `LLMConfig.to_dict`、`chat` 回退、异步默认 `NotImplementedError`。
   - `tests/async_workflow/test_llm_interface.py`：覆盖异步接口契约与配置字段兼容。
   - `tests/test_prompt.py`：新增顶层 `PromptFactory.build_prompt` 的异步 `chat` 流程测试。

### 验证命令

```bash
pdm run pytest
```

## 测试现状（已验证）

已在当前仓库执行：

```bash
pdm run pytest
```

结果：`38 passed in 0.18s`

覆盖模块包括：
- `background.py`
- `chain.py`
- `prompt.py`
- `llm/openai_llm.py`
- `llm/glm_llm.py`
- `util/cache.py`
- `util/random_name.py`
- `async_workflow/para_bus.py`
- `async_workflow/prompt.py`
- `async_workflow/workflow.py`

## R021-1 FlovoClient

`casevo.flovo_client.FlovoClient` 对齐 Flovo `WsEnvelope` 协议，提供同步执行、
流式回调执行和关闭三个 API。连接地址支持 `FLOVO_WS_URL` 环境变量覆盖（显式
参数优先），依赖仅使用已存在的 `websockets==16.0`，无新增第三方依赖。

```python
import asyncio
from casevo import FlovoClient

async def main():
    client = FlovoClient(url="ws://127.0.0.1:8090", timeout=30)
    result = await client.run_workflow("demo", {"model": "gpt"}, {"prompt": "hello"})
    print(result)
    events = []
    await client.run_workflow_stream("demo", {}, {"prompt": "hello"}, events.append)
    await client.close()

asyncio.run(main())
```

预期效果：客户端完成 `connect_ok → init_report → init_ok → send_input` 握手，
收集 `output` 并在 `workflow_finished` 后返回；流式模式依次回调 `data` 与 `finish`。
超时或连接失败会抛出 `FlovoError`（连接失败自动按 1/2/4 秒退避重试 3 次），
服务端提前断开也会转换为 `FlovoError`；握手响应 `message_id` 错配会记录 warning
并忽略，不会误当作有效响应。

## R021-2 Flovo agent_dialog 集成

`examples/flovo_integration/agent_dialog_demo.py` 使用 R021-1 提供的
`FlovoClient` 调用 Flovo `agent_dialog` 工作流，覆盖同步结果汇总、流式
`data -> finish` 回调，以及非空问题进入 Mock LLM、空问题进入 `[fallback]` 的
condition 两条路径。示例只编排输入和客户端调用，不在 Casevo 侧复制工作流逻辑。

Flovo 服务启动与示例运行：

```bash
cd /path/to/Flovo
RUSTFLAGS="-C linker=/usr/bin/gcc" cargo run -p flovo-ws --example server -- --config crates/flovo-ws/examples/dialog_workflow.json

cd /path/to/casevo-4-self
python examples/flovo_integration/agent_dialog_demo.py
```

默认连接 `ws://127.0.0.1:8090`，可通过 `FLOVO_WS_URL` 覆盖。预期同步调用返回
Mock 回答，流式调用至少产生一个 `status == "data"` 事件并以
`status == "finish"` 结束，空问题返回包含 `[fallback]` 的兜底结果。

真实服务集成测试位于 `tests/test_flovo_integration.py`，pytest marker 已注册为
`integration`：

```bash
pytest -m integration -v
```

测试验证同步输出、R021-1 尚未由真实服务覆盖的 output data 回调、同步/流式汇总
一致性及 condition 两路行为。服务未启动、连接超时或 `agent_dialog` 端点不可用时，
模块级探测会自动 skip；运行中若协议超时或连接中断，则由 `FlovoClient` 转换为
`FlovoError`，demo 会打印服务地址检查提示并正常关闭客户端。

## R024 集成示例升级（Casevo 侧）

当前分支为 `feature/R024-real-llm-demo`。运行示例前先启动 Flovo server；如需真实
LLM，配置 `FLOVO_LLM_API_KEY`，并可选配置 `FLOVO_LLM_BASE_URL`（默认
`https://api.openai.com/v1`）与 `FLOVO_LLM_MODEL`（默认 `gpt-4o-mini`），然后执行：

```bash
python examples/flovo_integration/agent_dialog_demo.py
```

配置密钥时，Flovo 的 `llm_call` 使用真实 OpenAI 兼容接口；未配置密钥时自动降级为
mock。无 context 时 mock 输出为 `[mock] <question>`；传入
`{"user_name": "alice", "tone": "formal"}` 后，R024 的 `build_prompt` 节点会把
画像字段拼入 prompt，输出应包含 `alice` 与 `formal`。若 Flovo server 不可用，
集成测试通过 `require_flovo_server` 自动 skip。

## R023 上下文桥接（Casevo 侧）

`FlovoClient.run_workflow` 与 `run_workflow_stream` 支持可选 `context` 字典，
客户端会将其作为 `send_input` 信封 `info.context` 传给 Flovo：

```python
from casevo import FlovoClient
from casevo.context_manager import ContextManager

context = ContextManager(
    initial_context={"user_name": "alice", "tone": "formal"}
).to_dict()
result = await FlovoClient().run_workflow(
    "agent_dialog",
    {},
    {"question": "Hello"},
    context=context,
)
```

R024 起，Flovo 的 `build_prompt` 节点读取 `context.<field>` 并将字段拼入 prompt，
因此带 context 的输出会区别于无 context 的输出。`context` 必须是字典，否则抛出
`TypeError`；传入 `None` 或空字典时不增加信封字段。

## R026 日志流 WebSocket 推送

`casevo.util.log_stream_server.LogStreamServer` 是 `TotLogStream` 的轻量网络适配器：
服务在守护线程中运行独立 asyncio 事件循环，客户端连接后自动订阅日志；每个连接
拥有独立队列，事件以 `{"status": "data", "event": {...}}` JSON 消息广播给所有客户端。
`websockets==16.0` 为既有传递依赖，R026 未修改项目依赖声明。

启动服务并连接客户端：

```python
import asyncio
import websockets
from casevo.util.log_stream_server import LogStreamServer
from casevo.util.tot_log_stream import TotLogStream

async def receive():
    async with websockets.connect("ws://127.0.0.1:8765") as ws:
        await asyncio.sleep(0.1)  # 等待服务端连接处理器完成自动订阅
        TotLogStream.add_model_log(1, "thought", "hello")
        print(await ws.recv())

server = LogStreamServer()
server.start()
asyncio.run(receive())
server.stop()
```

随后调用 `TotLogStream.add_model_log(...)` 或 `add_agent_log(...)`，客户端会收到类似：

```json
{"status":"data","event":{"ts":1,"owner":"model","type":"thought","item":"hello"}}
```

服务未启动时不会创建线程、事件循环或订阅。重复 `start()` / `stop()` 是幂等的，停止后
可以再次启动。客户端断开、发送失败或任务取消时，连接处理器会在 `finally` 中调用
`TotLogStream.unsubscribe`；停止服务还会关闭监听器和所有现有连接。端口绑定失败会由
`start()` 抛出 `RuntimeError`（原始异常作为 cause），单个客户端异常只记录日志并清理自身，
不会影响其他连接或 `TotLogStream` 的同步日志写入。

## R011 实现记录（2026-04-08）

### 目标

在 `src/casevo/llm/` 下新增可直接使用的 OpenAI 与 GLM 适配实现，满足 `LLM_INTERFACE` 抽象契约，并补齐测试与文档。

### 变更说明

1. 新增 LLM 模块
   - 新增 `src/casevo/llm/openai_llm.py`
     - `OpenAI_LLM` 实现 `send_message` / `send_embedding` / `get_lang_embedding`
     - 新增 `send_message_by_config`（映射 `LLMConfig` 字段）
     - 新增 `send_message_with_tools`（支持 OpenAI Function Calling）
     - 新增 `OpenAIEmbeddingFunction`，可直接传给 ChromaDB
   - 新增 `src/casevo/llm/glm_llm.py`
     - `GLM_LLM` 复用 OpenAI 兼容实现
     - 默认端点：`https://open.bigmodel.cn/api/paas/v4`
     - 默认聊天模型：`glm-4`
     - 默认 embedding 模型：`embedding-3`
   - 新增 `src/casevo/llm/__init__.py` 并在 `src/casevo/__init__.py` 导出 `OpenAI_LLM`、`GLM_LLM`

2. 测试新增
   - `tests/llm/test_openai_llm.py`
   - `tests/llm/test_glm_llm.py`
   - 使用 `unittest.mock` 模拟 `OpenAI` 客户端，覆盖：
     - 初始化参数
     - `send_message` 返回格式
     - `send_message_by_config` 配置映射
     - `send_embedding` 返回格式
     - `get_lang_embedding` 可调用性

3. 依赖与文档更新
   - `pyproject.toml` 新增可选依赖组：
     - `openai = ["openai>=1.0.0"]`
     - `glm = ["openai>=1.0.0", "zhipuai>=2.1.5"]`
   - `README.md` 新增“6. LLM 快速接入”章节（OpenAI/GLM 使用示例）

### 安装命令

```bash
pdm add openai
pdm add zhipuai
```

### 运行示例（输入与预期效果）

```python
from casevo.llm import OpenAI_LLM

llm = OpenAI_LLM(api_key="YOUR_OPENAI_KEY")
text = llm.send_message("请简要介绍 Casevo")
print(text)  # 预期：返回一段模型文本（str）

vectors = llm.send_embedding(["hello", "casevo"])
print(type(vectors), len(vectors), len(vectors[0]))  # 预期：list, N, embedding_dim
```

### 异常与处理策略

1. 未安装 `openai` 依赖
   - 触发点：实例化 `OpenAI_LLM` / `GLM_LLM`
   - 处理：抛出 `ImportError` 并提示安装 `pdm add openai`

2. `prompt` 类型非法
   - 触发点：`send_message` / `send_message_by_config` 输入不是 `str` 或 `list`
   - 处理：抛出 `TypeError("prompt must be str or list[dict]")`

3. 上游 API 请求失败（网络/鉴权/配额）
   - 触发点：`chat.completions.create` / `embeddings.create`
   - 处理：异常上抛，由业务层统一重试或熔断（保持基础 SDK 行为透明）

## 当前已确认风险 / 待修复点

1. 历史命名拼写保留（例如 `MemeoryFactory`、`OrederTypeActivation`），当前为兼容性命名，后续如修正建议通过别名+渐进迁移处理，避免破坏已有调用。

## 使用建议

1. 新增功能优先放入 `async_workflow/` 并保持同步 API 向后兼容。
2. 与 LLM 对接时优先实现 `LLM_INTERFACE` 的最小三方法集合（`send_message`、`send_embedding`、`get_lang_embedding`）。
3. 运行多轮实验前清理日志目录（`TotLogStream` 采用追加写入）。

## R020 实现记录（2026-04-16）

### 参考文档

项目的上下文主要在根目录 `CLAUDE.md` 中。

### 目标

在 `examples/async_workflow/` 下补充异步工作流示例，覆盖基础 `BaseStepNode` 编排与 `BaseStreamNode` 流式输出场景，帮助用户快速理解核心 API 使用方式。

### 变更说明

1. 新增 `examples/async_workflow/basic_workflow.py`
   - 展示 `WorkFlow` 初始化与 `set_input_parameters` 输入定义。
   - 展示自定义节点（继承 `BaseStepNode`）并声明：
     - `input_parameters`
     - `output_parameters`
     - `choices`
   - 展示节点核心方法使用：
     - `run()`
     - `wait_for_event()`
     - `get_input()` / `set_output()`
     - `set_choice()`
   - 展示 `set_nodes_list()`、`set_start_node()` 与 `asyncio.run()` 执行链路。

2. 新增 `examples/async_workflow/streaming_workflow.py`
   - 展示 `BaseStreamNode`（`stream_type="start"`）作为流式起始节点。
   - 展示 `output_parameters={"delta": "stream"}` 的流式参数定义。
   - 展示 recall 回调处理每个 token，并写入 `ParameterBus` 广播给下游。
   - 展示下游节点消费 stream 参数并聚合最终结果。
   - 示例使用 `MockStreamLLM.chat_stream` 模拟流式输出，避免依赖未合并逻辑与外部服务。

3. 新增 `examples/async_workflow/README.md`
   - 解释核心概念：`WorkFlow`、`BaseNode`、`ParameterBus`。
   - 提供快速开始、文件说明、输入示例与预期效果。
   - 环境变量配置复用 `examples/.env.example`，未重复创建样例文件。

### 依赖安装命令

```bash
pdm install -G example
pdm add openai
```

### 运行示例（输入与预期输出/效果）

```bash
pdm run python examples/async_workflow/basic_workflow.py
# 输入: x=3（代码内示例）
# 预期输出: [basic_workflow] result: {'z': 8}

pdm run python examples/async_workflow/streaming_workflow.py
# 输入: prompt=\"请简短问候\"（代码内示例）
# 预期效果: 控制台逐条输出 token，最终打印 {'answer': '你好，异步工作流！'}
```

### 可能异常与处理方式

1. 参数映射错误（`input_map` 指向不存在参数）
   - 触发点：`BaseNode.check_set_config()`
   - 处理：抛出异常并中止运行，提示缺失参数名。

2. 未设置起始节点
   - 触发点：`WorkFlow.run_all()`
   - 处理：抛出 `start node not set`，要求先执行 `set_start_node()`。

3. 工作流未完成就读取结果
   - 触发点：`WorkFlow.get_result()`
   - 处理：抛出 `workflow not finish!`，要求先等待 `run_all()` 执行结束。

## R025 日志流发布-订阅与 R006 自动清理

`TotLogStream` 支持通过 `subscribe` 注册同步回调，回调接收包含 `ts`、`owner`、
`type`、`item` 的事件字典；可按 owner 或 type 过滤，并通过 `unsubscribe` 退订。
订阅者快照在锁外派发，订阅列表由线程锁保护，因此回调内再次订阅或退订不会造成
死锁。单个回调抛出的异常会被记录并隔离，不影响后续回调和日志写入。

```python
from casevo.util.tot_log_stream import TotLogStream

subscription_id = TotLogStream.subscribe(lambda event: print(event), owner="model")
TotLogStream.init_log(agent_num=2, tar_folder="./logs", clear_old=True)
TotLogStream.add_model_log(1, "thought", "hello")
TotLogStream.unsubscribe(subscription_id)
```

`init_log(..., clear_old=True)` 会在初始化时删除目标目录中的 `model.txt`、所有
`agent_*.txt` 与 `event.txt`；默认 `clear_old=False` 保持原有 append 行为，旧文件
内容会被保留并继续追加。
