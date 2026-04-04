"""background.py 模块单元测试。"""

from __future__ import annotations

import threading
from types import SimpleNamespace

from casevo import background as background_module
from casevo.background import Background, BackgroundFactory, BackgroundItem


class DummyLLM:
    def get_lang_embedding(self):
        return object()


class DummyFactory:
    def __init__(self):
        self.last_add = None

    def __add_backgrounds__(self, add_list):
        self.last_add = add_list
        return "ok"


class DummyLock:
    def __init__(self):
        self.entered = 0
        self.exited = 0

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited += 1
        return False


class DummyCollection:
    def __init__(self):
        self._count = 0
        self.last_add = None
        self.last_query = None

    def count(self):
        return self._count

    def add(self, documents, metadatas, ids):
        self.last_add = {
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids,
        }
        self._count += len(documents)
        return {"ids": ids}

    def query(self, query_texts, n_results, where):
        self.last_query = {
            "query_texts": query_texts,
            "n_results": n_results,
            "where": where,
        }
        return SimpleNamespace(documents=[["hit-a", "hit-b"]])


def test_background_add_backgrounds_calls_factory_and_builds_items():
    """覆盖：add_backgrounds 调用正确工厂方法并填充默认字段。"""
    agent = SimpleNamespace(component_id="agent_1", context={})
    factory = DummyFactory()
    background = Background("agent_1_background", agent, factory)

    result = background.add_backgrounds(["doc-1", "doc-2"])

    assert result == "ok"
    assert factory.last_add is not None
    assert len(factory.last_add) == 2
    assert all(isinstance(item, BackgroundItem) for item in factory.last_add)
    assert factory.last_add[0].owner_id == "agent_1"
    assert factory.last_add[0].bg_type == "default"
    assert factory.last_add[0].extra == ""


def test_background_factory_init_creates_lock(monkeypatch):
    """覆盖：BackgroundFactory 初始化时创建 lock。"""

    class FakeClient:
        def __init__(self):
            self.collection = DummyCollection()

        def get_or_create_collection(self, name, embedding_function):
            assert name == "background"
            assert embedding_function is not None
            return self.collection

    monkeypatch.setattr(background_module.chromadb, "Client", lambda: FakeClient(), raising=False)

    model = SimpleNamespace(context={})
    factory = BackgroundFactory(DummyLLM(), background_num=3, model=model)

    assert isinstance(factory.lock, threading.Lock().__class__)
    assert factory.background_num == 3
    assert factory.background_collection is not None


def test_background_factory_add_and_search_with_lock():
    """覆盖：__add_backgrounds__ 与 __search_background__ 使用同一把锁并返回文档。"""
    factory = object.__new__(BackgroundFactory)
    factory.lock = DummyLock()
    factory.background_collection = DummyCollection()
    factory.background_num = 2

    add_res = factory.__add_backgrounds__(
        [
            BackgroundItem("agent_1", "policy", "doc-1", "x"),
            BackgroundItem("agent_1", "policy", "doc-2", "y"),
        ]
    )
    search_res = factory.__search_background__(["query"], "agent_1")

    assert add_res == {"ids": ["0", "1"]}
    assert factory.background_collection.last_add is not None
    assert factory.background_collection.last_query == {
        "query_texts": ["query"],
        "n_results": 2,
        "where": {"owner_id": "agent_1"},
    }
    assert search_res == [["hit-a", "hit-b"]]
    assert factory.lock.entered == 2
    assert factory.lock.exited == 2
