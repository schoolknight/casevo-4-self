"""chain.py 模块单元测试。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from casevo.chain import BaseStep, ThoughtChain


class EchoPrompt:
    """返回固定内容的 Prompt 假对象。"""

    def __init__(self, response: str):
        self.response = response

    def send_prompt(self, *_args, **_kwargs):
        return self.response


class RetryStep(BaseStep):
    """前几次故意失败，验证 ThoughtChain 重试逻辑。"""

    def __init__(self, step_id, tar_prompt, fail_times: int):
        super().__init__(step_id, tar_prompt)
        self.fail_times = fail_times
        self.calls = 0

    def after_process(self, input, response, agent=None, model=None):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise Exception("planned failure")
        return {"input": input, "last_response": response}


def _build_agent():
    """构造最小可用 Agent 假对象，满足 ThoughtChain 初始化依赖。"""
    return SimpleNamespace(
        component_id="agent1",
        context={"scene": "unit-test"},
        model=SimpleNamespace(context={"model": "mock"}),
    )


def test_thought_chain_run_and_get_output_success():
    """覆盖：链路正常执行、输出与历史读取。"""
    agent = _build_agent()
    step = BaseStep("s1", EchoPrompt("step-response"))
    chain = ThoughtChain(agent, [step])

    chain.set_input({"query": "hello"})
    chain.run_step()

    output = chain.get_output()
    history = chain.get_history()

    assert chain.status == "finish"
    assert output["last_response"] == "step-response"
    assert history[0]["id"] == "s1"


def test_get_output_before_finish_raises():
    """覆盖：未执行完成时读取输出应抛出异常。"""
    agent = _build_agent()
    chain = ThoughtChain(agent, [BaseStep("s1", EchoPrompt("ok"))])

    with pytest.raises(Exception, match="get output error"):
        chain.get_output()


def test_thought_chain_retry_success_after_failures():
    """覆盖：步骤失败后在 3 次重试内恢复成功。"""
    agent = _build_agent()
    step = RetryStep("retry", EchoPrompt("ok"), fail_times=2)
    chain = ThoughtChain(agent, [step])

    chain.set_input({"query": "hello"})
    chain.run_step()

    assert step.calls == 3
    assert chain.status == "finish"


def test_thought_chain_retry_failed_raises():
    """覆盖：步骤连续失败超过重试次数，链路抛出失败异常。"""
    agent = _build_agent()
    step = RetryStep("retry", EchoPrompt("never"), fail_times=3)
    chain = ThoughtChain(agent, [step])

    chain.set_input({"query": "hello"})

    with pytest.raises(Exception, match="Thought Chain Retry Failed"):
        chain.run_step()

    assert chain.status == "ready"
