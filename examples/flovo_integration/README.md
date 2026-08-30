# Flovo 集成示例

本示例通过 `casevo.flovo_client.FlovoClient` 调用 Flovo 的 `agent_dialog`
WebSocket 工作流。Python 侧只负责组装输入、调用客户端和展示输出；工作流节点、
condition 分支及 Mock LLM 均由 Flovo 配置定义。

## 前置条件

- Python 环境已安装 Casevo 项目依赖。
- 已安装 Rust 工具链。
- Flovo 仓库位于 `/home/jiangzx/project/Flovo`。
- 本机 Rust 构建需显式使用 GCC linker：`RUSTFLAGS="-C linker=/usr/bin/gcc"`。

## 运行步骤

1. 启动 Flovo WebSocket 服务：

```bash
cd /home/jiangzx/project/Flovo
RUSTFLAGS="-C linker=/usr/bin/gcc" cargo run -p flovo-ws --example server -- --config crates/flovo-ws/examples/dialog_workflow.json
```

2. 可选：覆盖默认服务地址 `ws://127.0.0.1:8090`：

```bash
export FLOVO_WS_URL=ws://127.0.0.1:8090
```

3. 在 Casevo 仓库根目录运行示例：

```bash
python examples/flovo_integration/agent_dialog_demo.py
```

## 预期输出

非空问题会进入 Mock LLM 分支。同步调用返回最终汇总结果；流式调用先收到至少一个
`data` 事件，并以 `finish` 事件结束：

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
