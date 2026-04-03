"""prompt.py 模块单元测试。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from casevo.prompt import PromptFactory


def test_prompt_factory_init_with_missing_folder_raises(dummy_llm):
    """验证：模板目录不存在时，工厂初始化抛出异常。"""
    with pytest.raises(Exception, match="prompt folder not exist"):
        PromptFactory("/path/not/exist", dummy_llm)


def test_get_template_with_missing_file_raises(tmp_path, dummy_llm):
    """验证：模板文件不存在时，get_template 抛出异常。"""
    factory = PromptFactory(str(tmp_path), dummy_llm)

    with pytest.raises(Exception, match="prompt file.*not exist"):
        factory.get_template("missing.txt")


def test_render_and_send_prompt_success(tmp_path, dummy_llm):
    """覆盖：模板加载、渲染变量注入、发送到 LLM 的完整流程。"""
    template = (
        "agent={{ agent.description }}|{{ agent.context }} "
        "model={{ model.context }} extra={{ extra.note }}"
    )
    (tmp_path / "greet.txt").write_text(template, encoding="utf-8")

    factory = PromptFactory(str(tmp_path), dummy_llm)
    prompt = factory.get_template("greet.txt")

    agent = SimpleNamespace(description="tester", context="agent-ctx")
    model = SimpleNamespace(context="model-ctx")

    result = prompt.send_prompt(ertra={"note": "ok"}, agent=agent, model=model)

    assert result == "mock-response:agent=tester|agent-ctx model=model-ctx extra=ok"
    assert dummy_llm.messages[-1] == "agent=tester|agent-ctx model=model-ctx extra=ok"
