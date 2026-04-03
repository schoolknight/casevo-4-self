"""pytest 基础夹具配置。"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


# 在测试环境注入最小 mesa stub，避免导入 casevo 包时的重依赖问题。
if "mesa" not in sys.modules:
    mesa_stub = types.ModuleType("mesa")

    class _Agent:
        def __init__(self, *args, **kwargs):
            pass

    class _Model:
        def __init__(self, *args, **kwargs):
            pass

    class _RandomActivation:
        def __init__(self, *args, **kwargs):
            pass

    class _RandomActivationByType(_RandomActivation):
        pass

    class _NetworkGrid:
        def __init__(self, *args, **kwargs):
            pass

    mesa_stub.Agent = _Agent
    mesa_stub.Model = _Model
    mesa_stub.time = types.SimpleNamespace(
        RandomActivation=_RandomActivation,
        RandomActivationByType=_RandomActivationByType,
    )
    mesa_stub.space = types.SimpleNamespace(NetworkGrid=_NetworkGrid)
    sys.modules["mesa"] = mesa_stub

# memory.py 在导入时依赖 chromadb；单元测试不覆盖其行为，这里提供空 stub 即可。
if "chromadb" not in sys.modules:
    sys.modules["chromadb"] = types.ModuleType("chromadb")


# 确保测试运行时可直接导入 src 下的 casevo 包。
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class DummyLLM:
    """用于测试 PromptFactory 的轻量 LLM 假对象。"""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_message(self, prompt_text: str) -> str:
        self.messages.append(prompt_text)
        return f"mock-response:{prompt_text}"


@pytest.fixture
def dummy_llm() -> DummyLLM:
    return DummyLLM()
