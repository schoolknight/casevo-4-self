"""异步工作流基础示例：展示 WorkFlow + BaseStepNode 的关键用法。"""

from __future__ import annotations

import asyncio
from typing import Any

from casevo.async_workflow import BaseStepNode, WorkFlow


class AddNode(BaseStepNode):
    """示例节点1：读取输入 x，计算 y=x+1。"""

    def __init__(self, config: dict[str, Any], workflow: WorkFlow):
        super().__init__(config, workflow)
        # 声明输入/输出参数类型：step 表示一次性参数。
        self.input_parameters = {"x": "step"}
        self.output_parameters = {"y": "step"}
        self.choices = ["next"]

    async def run(self, input_parameters: dict[str, Any] | None = None) -> bool:
        """执行节点逻辑。

        参数:
            input_parameters: 预留参数，当前示例不使用。
        返回:
            bool: True 表示执行成功。
        """
        # 等待工作流调度到当前节点。
        await self.wait_for_event()
        x = await self.get_input("x")
        await self.set_output("y", x + 1)
        self.set_choice("next")
        return True


class MultiplyNode(BaseStepNode):
    """示例节点2：读取输入 y，计算 z=y*2 并结束流程。"""

    def __init__(self, config: dict[str, Any], workflow: WorkFlow):
        super().__init__(config, workflow)
        self.input_parameters = {"y": "step"}
        self.output_parameters = {"z": "step"}
        self.choices = ["end"]

    async def run(self, input_parameters: dict[str, Any] | None = None) -> bool:
        """执行节点逻辑并产出最终结果。"""
        await self.wait_for_event()
        y = await self.get_input("y")
        await self.set_output("z", y * 2)
        self.set_choice("end")
        return True


async def run_basic_workflow(x_value: int) -> dict[str, Any]:
    """运行基础异步工作流。

    参数:
        x_value: 业务输入值。
    返回:
        dict[str, Any]: 工作流结束节点的输出结果。
    """
    workflow = WorkFlow(name="basic_demo", prompt_factory=None)

    # 工作流初始化输入定义（start 节点）。
    workflow.set_input_parameters({"x": "step"})

    # 节点配置结构示例：id/node_name/choice_map/attrs/input_map。
    add_node = AddNode(
        {
            "id": "n1",
            "node_name": "node_add",
            "choice_map": {"next": "node_multiply"},
            "attrs": {"desc": "x + 1"},
            "input_map": {"x": "start.x"},
        },
        workflow,
    )
    multiply_node = MultiplyNode(
        {
            "id": "n2",
            "node_name": "node_multiply",
            "choice_map": {"end": "finish"},
            "attrs": {"desc": "y * 2"},
            "input_map": {"y": "node_add.y"},
        },
        workflow,
    )

    add_node.check_set_config()
    multiply_node.check_set_config()

    # 注册节点并设置起始节点。
    workflow.set_nodes_list([add_node, multiply_node])
    workflow.set_start_node("node_add")

    # 注入运行输入并执行工作流。
    await workflow.set_input({"x": x_value})
    await workflow.run_all()
    return workflow.get_result()


def main() -> None:
    """通过 asyncio.run 启动异步工作流并打印结果。"""
    result = asyncio.run(run_basic_workflow(x_value=3))
    print("[basic_workflow] result:", result)  # 预期: {'z': 8}


if __name__ == "__main__":
    main()
