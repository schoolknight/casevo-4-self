from __future__ import annotations

import asyncio
from typing import Any


# 参数总线：负责节点间参数传递。
class ParameterBus:
    def __init__(self) -> None:
        self.parameter_dict: dict[str, dict[str, Any]] = {}
        self.msg_dict: dict[str, dict[str, asyncio.Queue]] = {}

    def init_output_parameter(self, node_name: str, target_output_dict: dict[str, str]) -> None:
        for parameter_name in target_output_dict:
            key = f"{node_name}.{parameter_name}"
            if target_output_dict[parameter_name] == "step":
                self.parameter_dict[key] = {
                    "type": "step",
                    "value": None,
                    "event": asyncio.Event(),
                }
            elif target_output_dict[parameter_name] == "stream":
                self.parameter_dict[key] = {
                    "type": "stream",
                }

    def register_input_parameter(self, node_name: str, tara_name: str) -> None:
        if tara_name not in self.parameter_dict:
            raise Exception("Not found parameter name:%s" % (tara_name))

        if self.parameter_dict[tara_name]["type"] != "stream":
            raise Exception(
                "parameter %s must be stream, but this is %s"
                % (tara_name, self.parameter_dict[tara_name]["type"])
            )

        if tara_name not in self.msg_dict:
            self.msg_dict[tara_name] = {node_name: asyncio.Queue()}
        else:
            self.msg_dict[tara_name][node_name] = asyncio.Queue()

    def check_parameter(self, node_name: str, tar_para: str) -> bool:
        return f"{node_name}.{tar_para}" in self.parameter_dict

    async def set_value(self, node_name: str, parameter_name: str, value: Any) -> None:
        cur_name = f"{node_name}.{parameter_name}"

        if cur_name not in self.parameter_dict:
            raise Exception("not found parameter name %s" % cur_name)

        if self.parameter_dict[cur_name]["type"] == "step":
            self.parameter_dict[cur_name]["value"] = value
            self.parameter_dict[cur_name]["event"].set()
        elif self.parameter_dict[cur_name]["type"] == "stream":
            for queue in self.msg_dict[cur_name].values():
                await queue.put(value)

    async def get_value(self, node_name: str, para_name: str):
        if para_name not in self.parameter_dict:
            raise Exception("not found parameter name %s" % para_name)

        if self.parameter_dict[para_name]["type"] == "step":
            await self.parameter_dict[para_name]["event"].wait()
            return self.parameter_dict[para_name]["value"]

        value = await self.msg_dict[para_name][node_name].get()
        self.msg_dict[para_name][node_name].task_done()
        return value

    def get_node_result(self, node_name: str) -> dict[str, Any]:
        tmp_result = {}
        for key in self.parameter_dict:
            if self.parameter_dict[key]["type"] != "stream" and key.startswith(f"{node_name}."):
                tmp_result[key[len(node_name) + 1 :]] = self.parameter_dict[key]["value"]
        return tmp_result
