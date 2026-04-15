"""context_manager.py 与 AgentBase 上下文集成测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from casevo.agent_base import AgentBase
from casevo.context_manager import ContextManager
from casevo.prompt import PromptFactory


class _DummyMemoryFactory:
    """最小内存工厂桩对象。"""

    @staticmethod
    def create_memory(_agent):
        return object()


class _DummyModel:
    """最小模型桩对象，满足 AgentBase 初始化依赖。"""

    def __init__(self):
        self.memory_factory = _DummyMemoryFactory()
        self.context = {"model": "unit-test"}


class _DemoAgent(AgentBase):
    """用于测试 AgentBase 的最小可实例化实现。"""

    def step(self):
        return None


def test_context_manager_init_and_get_copy():
    """覆盖：空初始化、带初始值初始化与 get 副本语义。"""
    empty = ContextManager()
    assert empty.get() == {}

    manager = ContextManager({"a": 1, "nested": {"x": 1}})
    copied = manager.get()
    copied["nested"]["x"] = 2
    assert manager.get_nested("nested.x") == 1


def test_context_manager_update_partial_fields():
    """覆盖：update 仅覆盖指定顶层字段。"""
    manager = ContextManager({"a": 1, "b": 2})
    manager.update({"b": 3, "c": 4})
    assert manager.to_dict() == {"a": 1, "b": 3, "c": 4}


def test_context_manager_merge_deep():
    """覆盖：merge 深度合并语义。"""
    manager = ContextManager(
        {"agent": {"name": "alice", "status": {"round": 1, "alive": True}}, "x": 1}
    )
    manager.merge({"agent": {"status": {"round": 2}, "role": "leader"}, "x": {"k": "v"}})
    assert manager.to_dict() == {
        "agent": {
            "name": "alice",
            "status": {"round": 2, "alive": True},
            "role": "leader",
        },
        "x": {"k": "v"},
    }


def test_context_manager_nested_get_set():
    """覆盖：点分路径读写与默认值。"""
    manager = ContextManager({"agent": {"status": {"alive": True}}})
    assert manager.get_nested("agent.status.alive") is True
    assert manager.get_nested("agent.status.round", default=0) == 0

    manager.set_nested("agent.status.round", 3)
    manager.set_nested("agent.profile.name", "alice")
    assert manager.to_dict()["agent"]["status"]["round"] == 3
    assert manager.to_dict()["agent"]["profile"]["name"] == "alice"


def test_context_manager_delete_and_clear():
    """覆盖：批量删除与清空。"""
    manager = ContextManager({"a": 1, "b": 2, "c": 3})
    manager.delete(["b", "missing"])
    assert manager.to_dict() == {"a": 1, "c": 3}

    manager.clear()
    assert manager.to_dict() == {}


def test_context_manager_input_validation():
    """覆盖：输入类型校验。"""
    manager = ContextManager()
    with pytest.raises(TypeError):
        manager.update([])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        manager.merge([])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        manager.get_nested("")
    with pytest.raises(ValueError):
        manager.set_nested("...", 1)


def test_agent_base_context_backward_compatible():
    """覆盖：AgentBase 上下文字段的读写兼容。"""
    agent = _DemoAgent(unique_id=1, model=_DummyModel(), description="demo", context={"a": 1})
    assert agent.context == {"a": 1}

    # 读取返回副本，不应影响内部真实上下文。
    copied = agent.context
    copied["a"] = 999
    assert agent.context == {"a": 1}

    # 旧写法仍可整体替换。
    agent.context = {"b": 2}
    assert agent.context == {"b": 2}

    # 新能力：通过 context_manager 做部分更新。
    agent.context_manager.update({"c": 3})
    assert agent.context == {"b": 2, "c": 3}


def test_prompt_reads_latest_agent_context(tmp_path: Path, dummy_llm):
    """覆盖：Prompt 系统读取到 ContextManager 更新后的上下文。"""
    template_file = tmp_path / "demo_prompt.txt"
    template_file.write_text("{{ agent.context['state'] }}", encoding="utf-8")

    factory = PromptFactory(str(tmp_path), dummy_llm)
    prompt = factory.get_template("demo_prompt.txt")
    agent = _DemoAgent(
        unique_id=1,
        model=_DummyModel(),
        description="demo",
        context={"state": "init"},
    )
    agent.context_manager.update({"state": "updated"})

    result = prompt.send_prompt(agent=agent, model=agent.model)
    assert result == "mock-response:updated"
