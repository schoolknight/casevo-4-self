# Flovo 集成示例

本示例通过 `casevo.flovo_client.FlovoClient` 调用 Flovo 的 `agent_dialog`
WebSocket 工作流。Python 侧只负责组装输入、调用客户端和展示输出；工作流节点、
condition 分支及 Mock LLM 均由 Flovo 配置定义。

## 前置条件

- Python 环境已安装 Casevo 项目依赖。
- 已安装 Rust 工具链。
- Flovo 仓库已检出到本机任意目录，并通过下方 `FLOVO_REPO` 环境变量指定。
- 本机 Rust 构建需显式使用 GCC linker：`RUSTFLAGS="-C linker=/usr/bin/gcc"`。

## 运行步骤

1. 设置 Flovo 仓库路径并启动 WebSocket 服务：

```bash
export FLOVO_REPO=/path/to/Flovo
cd "$FLOVO_REPO"
RUSTFLAGS="-C linker=/usr/bin/gcc" cargo run -p flovo-ws --example server -- --config crates/flovo-ws/examples/dialog_workflow.json
```

2. 可选：配置真实 LLM。设置 `FLOVO_LLM_API_KEY` 后，Flovo 的 `llm_call`
   使用 OpenAI 兼容接口；未配置时自动使用 mock，示例仍可直接运行：

```bash
export FLOVO_LLM_API_KEY=your-api-key
export FLOVO_LLM_BASE_URL=https://api.openai.com/v1
export FLOVO_LLM_MODEL=gpt-4o-mini
```

可选：若服务不是默认地址 `ws://127.0.0.1:8090`，另行设置：

```bash
export FLOVO_WS_URL=ws://127.0.0.1:8090
```

3. 在 Casevo 仓库根目录运行示例：

```bash
python examples/flovo_integration/agent_dialog_demo.py
```

## 预期输出

未配置密钥时，非空问题会进入 Mock LLM 分支。同步调用返回最终汇总结果；流式调用
先收到至少一个 `data` 事件，并以 `finish` 事件结束：

```text
=== Sync: non-empty question (LLM path) ===
result: ['WHAT CAN FLOVO DO?', '[mock complete]']

=== Stream: non-empty question (data -> finish) ===
event: {'status': 'data', 'content': 'WHAT CAN FLOVO DO?'}
event: {'status': 'data', 'content': '[mock complete]'}
event: {'status': 'finish', 'content': ['WHAT CAN FLOVO DO?', '[mock complete]']}

=== Sync: empty question (fallback path) ===
result: [fallback] no question provided
```

配置 `FLOVO_LLM_API_KEY` 后，非空问题改走真实 LLM，返回内容由模型生成；
`FLOVO_LLM_BASE_URL` 默认是 `https://api.openai.com/v1`，`FLOVO_LLM_MODEL`
默认是 `gpt-4o-mini`。密钥只从环境变量读取，示例不会打印密钥内容。

实际结果的外层结构可能是字典或列表，取决于 Flovo 工作流发送的 output 数量：单个
output 直接返回其内容，多个 output 按到达顺序汇总为列表。

## 运行集成测试

保持 Flovo 服务运行，然后执行：

```bash
pytest -m integration -v
```

服务运行时，测试覆盖同步返回、`data -> finish` 回调序列、同步与流式结果一致性，
以及 condition 的两条路径。服务未运行或 `agent_dialog` 不可用时，集成测试会自动
skip，而不是报错。

空 `question` 进入 `[fallback]` 分支；示例中的非空问题包含问号，进入 Mock LLM
流式回答分支。该测试同时补齐 R021-1 `FlovoClient` 已实现但尚未由真实服务验证的
output `data` 回调行为。

## 真实 LLM 配置

| 环境变量 | 是否必填 | 默认值 | 说明 |
|---|---|---|---|
| `FLOVO_LLM_API_KEY` | 是（真实 LLM） | 无 | OpenAI 兼容接口密钥；缺省时降级为 mock |
| `FLOVO_LLM_BASE_URL` | 否 | `https://api.openai.com/v1` | OpenAI 兼容服务地址 |
| `FLOVO_LLM_MODEL` | 否 | `gpt-4o-mini` | 聊天模型名称 |

## 上下文个性化

Casevo 可将 agent 上下文作为 JSON 随 `send_input` 信封传给 Flovo：

```python
context = {"user_name": "alice", "tone": "formal"}
result = await client.run_workflow(
    "agent_dialog",
    {},
    {"user_id": "user-demo", "session_id": "session-demo", "question": "Hello"},
    context=context,
)
```

Flovo 的 `build_prompt` 节点使用 `context.<field>` 读取上下文，并将用户画像拼入
`llm_call` 的 prompt。带上下文时，输出会体现 `alice` 和 `formal` 等画像字段；
不传 `context` 时，prompt 退化为原始 `question`，mock 输出也保持 `[mock] <question>`。
语法对应 Flovo 的 `NodeHelper.get_input`。
