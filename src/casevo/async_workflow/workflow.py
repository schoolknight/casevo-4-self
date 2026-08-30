"""⚠️ DEPRECATED (2026-08-30)：本模块将由 Flovo 引擎（https://github.com/rgCASS/Flovo）
取代。请通过 casevo.flovo_client.FlovoClient 接入（见 examples/flovo_integration/）。
不再新增功能，仅修复致命 Bug。"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import os
from typing import Any, Optional

from .node import BaseNode
from .para_bus import ParameterBus
from .prompt import PromptFactory


# 异步工作流运行时。
class WorkFlow:
    def __init__(self, name: str, prompt_factory: PromptFactory):
        self.name = name
        self.node_dict: dict[str, dict[str, Any]] = {}
        self.start_node_name: Optional[str] = None

        self.status = "init"
        self.result: Optional[dict[str, Any]] = None
        self.finish_node: Optional[str] = None

        self.context: dict[str, Any] = {}
        self.memory: dict[str, Any] = {}

        self.prompt_factory = prompt_factory
        self.parameter_bus = ParameterBus()

        self.msg_entry_node = None
        self.msg_queue: asyncio.Queue = asyncio.Queue()

    def set_context(self, key: str, value: Any) -> None:
        self.context[key] = value

    def get_context(self, key: str):
        if key in self.context:
            return self.context[key]
        raise Exception("key not found in context")

    def set_nodes_list(self, node_list: list[BaseNode]) -> None:
        for node in node_list:
            self.node_dict[node.name] = {
                "node": node,
                "event": asyncio.Event(),
                "task": None,
            }
            self.parameter_bus.init_output_parameter(node.name, node.output_parameters)
        self.status = "ready"

    def choose_node(self, cur_node: str, node_name: str) -> None:
        if node_name != "finish":
            self.node_dict[node_name]["event"].set()
        else:
            self.result = self.parameter_bus.get_node_result(cur_node)
            self.finish_node = cur_node
            self.status = "finish"

    def cancel_node(self, node_name: str) -> None:
        if node_name != "finish" and node_name in self.node_dict:
            if not self.node_dict[node_name]["node"].is_key_node():
                task = self.node_dict[node_name]["task"]
                if task is not None:
                    task.cancel()

    def get_result(self) -> dict[str, Any]:
        if self.status != "finish":
            raise Exception("workflow not finish!")
        return self.result or {}

    def set_start_node(self, node_name: str) -> None:
        self.start_node_name = node_name

    def set_input_parameters(self, input_parameters: dict[str, str]) -> None:
        self.parameter_bus.init_output_parameter("start", input_parameters)

    async def set_input(self, input_dict: dict[str, Any]) -> None:
        for key, value in input_dict.items():
            if not self.parameter_bus.check_parameter("start", key):
                raise Exception("Error: " + key + " not found!")
            await self.parameter_bus.set_value("start", key, value)

    def set_memory(self, key: str, value: Any) -> None:
        self.memory[key] = value

    def get_memory(self, key: str):
        if key in self.memory:
            return self.memory[key]
        return None

    async def add_message(self, msg: dict[str, Any]) -> None:
        await self.msg_queue.put(msg)

    async def get_message(self):
        value = await self.msg_queue.get()
        self.msg_queue.task_done()
        return value

    async def wait_for_event(self, node_name: str):
        if node_name not in self.node_dict:
            raise Exception(f"Node {node_name} does not exist in the workflow.")
        return await self.node_dict[node_name]["event"].wait()

    async def run_standalone(self, tar_node: BaseNode):
        try:
            result_status = await tar_node.run()
            if not result_status:
                raise Exception("Something went wrong when run the node.")
        except asyncio.CancelledError:
            return

    async def run_all(self):
        if self.status != "ready":
            raise Exception("workflow not ready")

        if not self.start_node_name:
            raise Exception("start node not set")

        self.status = "running"
        task_list = []

        for node_name in self.node_dict:
            cur_node = self.node_dict[node_name]["node"]
            if cur_node.runable():
                cur_task = asyncio.create_task(cur_node.run_withlog())
                self.node_dict[node_name]["task"] = cur_task
                task_list.append(cur_task)

        self.choose_node("start", self.start_node_name)
        await asyncio.gather(*task_list, return_exceptions=True)

    def log(self, log_type: str, msg: str) -> None:
        logger = self.context.get("logger")
        if logger is None:
            return

        if log_type == "info":
            logger.info(msg)
        elif log_type == "error":
            logger.error(msg)
        elif log_type == "warning":
            logger.warning(msg)
        elif log_type == "debug":
            logger.debug(msg)
        else:
            logger.info(msg)


class WorkflowManager:
    def __init__(self, config_file_dir: str, prompt_factory: PromptFactory):
        self.workflow_config: dict[str, Any] = {}
        for filename in os.listdir(config_file_dir):
            if filename.endswith(".json"):
                config_path = os.path.join(config_file_dir, filename)
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    for name in config_data:
                        if name in self.workflow_config:
                            raise ValueError(f"重复的工作流名称 '{name}' 在文件 {filename} 中")
                    self.workflow_config.update(config_data)

        self.class_registry: dict[str, type[BaseNode]] = {}
        self.prompt_factory = prompt_factory

    def register_nodes_from_directory(self, directory: str):
        abs_directory = os.path.abspath(directory)

        if not os.path.exists(abs_directory):
            return

        pre_path = directory.replace("/", ".")
        if pre_path.endswith("."):
            pre_path = pre_path[:-1]

        for filename in os.listdir(abs_directory):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                module_path = f"{pre_path}.{module_name}"
                try:
                    module = importlib.import_module(module_path)
                    for _, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and hasattr(obj, "_decorated_by_register_class"):
                            for alia in obj._alias:
                                self.class_registry[alia] = obj
                except Exception:
                    continue

    def build_workflow(self, name: str, logger=None) -> WorkFlow:
        if name not in self.workflow_config:
            raise ValueError(f"Workflow '{name}' not found in configuration.")

        cur_workflow = WorkFlow(name, self.prompt_factory)
        cur_workflow.set_context("logger", logger)
        cur_workflow.set_input_parameters(self.workflow_config[name]["input_parameters"])

        node_list = []
        for item in self.workflow_config[name]["nodes"]:
            if item["node_type"] not in self.class_registry:
                raise ValueError(f"Node type '{item['node_type']}' not registered.")

            cur_node = self.class_registry[item["node_type"]](item, cur_workflow)
            cur_node.check_set_config()
            node_list.append(cur_node)

        cur_workflow.set_nodes_list(node_list)
        cur_workflow.set_start_node(self.workflow_config[name]["start_node"])
        return cur_workflow
