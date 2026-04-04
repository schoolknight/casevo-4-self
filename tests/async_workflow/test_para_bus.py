"""async_workflow/para_bus.py 模块单元测试。"""

from __future__ import annotations

import asyncio

from casevo.async_workflow.para_bus import ParameterBus


def test_step_parameter_set_and_get_success():
    bus = ParameterBus()
    bus.init_output_parameter("n1", {"out": "step"})

    async def runner():
        await bus.set_value("n1", "out", 123)
        return await bus.get_value("consumer", "n1.out")

    value = asyncio.run(runner())
    assert value == 123


def test_stream_parameter_broadcast_success():
    bus = ParameterBus()
    bus.init_output_parameter("producer", {"stream_out": "stream"})
    bus.register_input_parameter("c1", "producer.stream_out")
    bus.register_input_parameter("c2", "producer.stream_out")

    async def runner():
        await bus.set_value("producer", "stream_out", "hello")
        v1 = await bus.get_value("c1", "producer.stream_out")
        v2 = await bus.get_value("c2", "producer.stream_out")
        return v1, v2

    got1, got2 = asyncio.run(runner())
    assert got1 == "hello"
    assert got2 == "hello"
