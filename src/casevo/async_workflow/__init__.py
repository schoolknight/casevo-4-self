"""⚠️ DEPRECATED (2026-08-30)：本模块将由 Flovo 引擎（https://github.com/rgCASS/Flovo）
取代。请通过 casevo.flovo_client.FlovoClient 接入（见 examples/flovo_integration/）。
不再新增功能，仅修复致命 Bug。"""

from casevo.async_workflow.llm_interface import LLMConfig, LLM_INTERFACE
from casevo.async_workflow.node import BaseNode, BaseStepNode, BaseStreamNode, NodeType
from casevo.async_workflow.para_bus import ParameterBus
from casevo.async_workflow.prompt import (
    PromptBase,
    PromptChat,
    PromptChatStream,
    PromptFactory,
    PromptIntentAnalysis,
)
from casevo.async_workflow.register_node import register_class
from casevo.async_workflow.workflow import WorkFlow, WorkflowManager

__all__ = [
    "LLMConfig",
    "LLM_INTERFACE",
    "NodeType",
    "BaseNode",
    "BaseStepNode",
    "BaseStreamNode",
    "ParameterBus",
    "PromptBase",
    "PromptChat",
    "PromptChatStream",
    "PromptIntentAnalysis",
    "PromptFactory",
    "register_class",
    "WorkFlow",
    "WorkflowManager",
]
