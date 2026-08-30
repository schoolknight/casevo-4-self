"""async_workflow 废弃标记与兼容性测试。"""

from __future__ import annotations

import ast
from pathlib import Path


def test_async_workflow_modules_remain_importable():
    import casevo.async_workflow
    from casevo.async_workflow import (
        llm_interface,
        node,
        para_bus,
        prompt,
        register_node,
        workflow,
    )

    assert all(module is not None for module in (
        casevo.async_workflow,
        workflow,
        node,
        para_bus,
        prompt,
        register_node,
        llm_interface,
    ))


def test_async_workflow_modules_have_deprecation_docstrings():
    package_dir = Path(__file__).parents[1] / "src" / "casevo" / "async_workflow"
    module_names = (
        "__init__.py",
        "node.py",
        "register_node.py",
        "para_bus.py",
        "prompt.py",
        "workflow.py",
        "llm_interface.py",
    )

    for module_name in module_names:
        source = (package_dir / module_name).read_text(encoding="utf-8")
        module = ast.parse(source, filename=module_name)
        docstring = ast.get_docstring(module, clean=False) or ""
        assert "DEPRECATED" in docstring
        assert "2026-08-30" in docstring


def test_async_workflow_public_api_remains_usable():
    from casevo.async_workflow import WorkFlow

    workflow = WorkFlow("compatibility", prompt_factory=None)

    assert workflow.name == "compatibility"
    assert workflow.status == "init"
