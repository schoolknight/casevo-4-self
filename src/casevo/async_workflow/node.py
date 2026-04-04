from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Any


# 工作流节点类型定义。
class NodeType(Enum):
    BaseNode = 0
    StepNode = 1
    StreamNode = 2


# 工作流节点基类。
class BaseNode:
    def __init__(self, config: dict[str, Any], workflow, node_type: NodeType = NodeType.BaseNode):
        self.input_parameters: dict[str, str] = {}
        self.output_parameters: dict[str, str] = {}
        self.choices: list[str] = []

        self.id = config["id"]
        self.name = config["node_name"]
        self.node_type = node_type
        self.choice_map = config["choice_map"]
        self.attrs = config["attrs"]
        self.parent_workflow = workflow
        self.input_map = config["input_map"]
        self.key_node = bool(config.get("key_node", False))

    def check_set_config(self) -> bool:
        if set(self.choice_map.keys()) != set(self.choices):
            self.parent_workflow.log("error", f"The choices of the {self.name} node not exists.")
            raise Exception(f"The choices of the {self.name} node not exists.")

        self.parent_workflow.parameter_bus.init_output_parameter(self.name, self.output_parameters)
        for cur_key in self.input_parameters:
            if cur_key not in self.input_map:
                self.parent_workflow.log(
                    "error",
                    f"The {cur_key} parameter is missing from the input config!",
                )
                raise NameError(f"The {cur_key} parameter is missing from the input config!")
            if self.input_parameters[cur_key] == "stream":
                self.parent_workflow.parameter_bus.register_input_parameter(self.name, self.input_map[cur_key])

        self.parent_workflow.log(
            "debug",
            f"check node {self.name}, input_parameters={self.input_parameters}, input_map={self.input_map}",
        )
        return True

    async def get_input(self, para_name: str):
        if para_name not in self.input_parameters:
            self.parent_workflow.log(
                "error",
                f"The {para_name} parameter not exists in the {self.name} parameter bus.",
            )
            raise Exception(f"The {para_name} parameter not exists in the {self.name} parameter bus.")

        if not self.input_map[para_name]:
            return None

        return await self.parent_workflow.parameter_bus.get_value(self.name, self.input_map[para_name])

    async def set_output(self, para_name: str, value: Any) -> None:
        if para_name not in self.output_parameters:
            self.parent_workflow.log(
                "error",
                f"The {para_name} parameter not exists in the {self.name} parameter bus.",
            )
            raise Exception(f"The {para_name} parameter not exists in the {self.name} parameter bus.")

        await self.parent_workflow.parameter_bus.set_value(self.name, para_name, value)

    @abstractmethod
    async def run(self, input_parameters: dict[str, Any] | None = None):
        pass

    async def run_withlog(self, input_parameters: dict[str, Any] | None = None):
        self.parent_workflow.log("debug", f"run node name={self.name}, node_type={self.node_type}")
        await self.run(input_parameters or {})

    async def get_message(self):
        self.parent_workflow.log("debug", f"get_message={self.name}")
        return await self.parent_workflow.get_message()

    def runable(self) -> bool:
        return True

    def set_choice(self, choice_name: str) -> str:
        if choice_name not in self.choice_map:
            self.parent_workflow.log("error", f"The choice '{choice_name}' not exists.")
            raise Exception(f"The choice '{choice_name}' not exists.")

        node_choice = self.choice_map[choice_name]
        self.parent_workflow.choose_node(self.name, node_choice)

        for cur_choice in self.choice_map:
            tmp_node = self.choice_map[cur_choice]
            if tmp_node != node_choice:
                self.parent_workflow.cancel_node(tmp_node)

        return node_choice

    def is_key_node(self) -> bool:
        return self.key_node

    async def wait_for_event(self):
        await self.parent_workflow.wait_for_event(self.name)


class BaseStepNode(BaseNode):
    def __init__(self, config, workflow):
        super().__init__(config, workflow, NodeType.StepNode)


class BaseStreamNode(BaseNode):
    def __init__(self, config, workflow):
        super().__init__(config, workflow, NodeType.StreamNode)
        self.recall = None
        self.stream_type = config["stream_type"]

    def runable(self) -> bool:
        return self.stream_type == "start"

    def set_recall(self, recall) -> None:
        self.recall = recall
