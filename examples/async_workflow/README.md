# 异步工作流示例

本目录展示 Casevo `async_workflow` 的两个典型场景：基础节点编排与流式输出处理。

## 核心概念

- `WorkFlow`：异步工作流运行时，负责节点调度、状态管理与结果汇总。
- `BaseNode`：节点抽象基类，封装参数读写、事件等待、分支跳转等能力。
- `ParameterBus`：参数总线，负责节点间 `step/stream` 两类参数传递。

## 快速开始

1. 安装依赖

```bash
pdm install -G example
```

如需接入真实 OpenAI 流式对话：

```bash
pdm add openai
```

2. 配置环境变量（复用已有示例）

```bash
cp examples/.env.example examples/.env
```

3. 运行示例

```bash
pdm run python examples/async_workflow/basic_workflow.py
pdm run python examples/async_workflow/streaming_workflow.py
```

## 文件说明

- `basic_workflow.py`
  - 演示 `WorkFlow` 初始化、`set_nodes_list`、`set_start_node`。
  - 演示自定义 `BaseStepNode` 的 `input_parameters` / `output_parameters` / `choices`。
  - 演示 `run()`、`wait_for_event()`、`get_input()`、`set_output()`、`set_choice()`。

- `streaming_workflow.py`
  - 演示 `BaseStreamNode` 与 `BaseStepNode` 的配合使用。
  - 演示 `stream_type="start"` 的启动语义。
  - 演示 `output_parameters` 为 `"stream"` 的流式参数。
  - 演示通过 `recall` 回调接收 token 并广播到下游节点。

## 运行示例（输入与预期效果）

1. 基础工作流
- 输入：`x=3`
- 预期输出：`{'z': 8}`

2. 流式工作流
- 输入：`prompt="请简短问候"`
- 预期效果：控制台逐条打印 token，最终输出聚合结果：`{'answer': '你好，异步工作流！'}`

## 常见异常

- 节点参数映射错误（如 `input_map` 引用不存在）
  - 表现：`check_set_config()` 抛异常。
  - 处理：检查参数名与上游节点输出是否一致。

- 未设置起始节点
  - 表现：`run_all()` 报错 `start node not set`。
  - 处理：调用 `workflow.set_start_node(...)`。

- 工作流未结束即取结果
  - 表现：`get_result()` 报错 `workflow not finish!`。
  - 处理：确保 `await workflow.run_all()` 完成后再取结果。
