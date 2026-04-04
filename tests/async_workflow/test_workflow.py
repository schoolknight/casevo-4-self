"""async_workflow/workflow.py 模块单元测试。"""

from __future__ import annotations

import asyncio

from casevo.async_workflow.node import BaseStepNode
from casevo.async_workflow.workflow import WorkFlow


class StartNode(BaseStepNode):
    def __init__(self, config, workflow):
        super().__init__(config, workflow)
        self.input_parameters = {"x": "step"}
        self.output_parameters = {"y": "step"}
        self.choices = ["next"]

    async def run(self, input_parameters=None):
        await self.wait_for_event()
        x = await self.get_input("x")
        await self.set_output("y", x + 1)
        self.set_choice("next")
        return True


class EndNode(BaseStepNode):
    def __init__(self, config, workflow):
        super().__init__(config, workflow)
        self.input_parameters = {"y": "step"}
        self.output_parameters = {"z": "step"}
        self.choices = ["end"]

    async def run(self, input_parameters=None):
        await self.wait_for_event()
        y = await self.get_input("y")
        await self.set_output("z", y * 2)
        self.set_choice("end")
        return True


def test_workflow_run_all_and_get_result_success():
    workflow = WorkFlow("demo", prompt_factory=None)
    workflow.set_input_parameters({"x": "step"})

    node1 = StartNode(
        {
            "id": "n1",
            "node_name": "node_start",
            "choice_map": {"next": "node_end"},
            "attrs": {},
            "input_map": {"x": "start.x"},
        },
        workflow,
    )
    node2 = EndNode(
        {
            "id": "n2",
            "node_name": "node_end",
            "choice_map": {"end": "finish"},
            "attrs": {},
            "input_map": {"y": "node_start.y"},
        },
        workflow,
    )

    node1.check_set_config()
    node2.check_set_config()
    workflow.set_nodes_list([node1, node2])
    workflow.set_start_node("node_start")

    async def runner():
        await workflow.set_input({"x": 3})
        await workflow.run_all()
        return workflow.get_result()

    result = asyncio.run(runner())
    assert workflow.status == "finish"
    assert result == {"z": 8}
