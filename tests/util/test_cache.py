"""util/cache.py 模块单元测试。"""

from __future__ import annotations

from casevo.util.cache import RequestCache


def test_request_cache_add_and_hit(tmp_path):
    """覆盖：缓存写入后可命中并返回正确响应。"""
    db_path = tmp_path / "request_cache.db"
    cache = RequestCache(str(db_path))

    cache.add_request_cache("hello", "world")

    assert cache.get_request_cache("hello") == "world"


def test_request_cache_miss_returns_none(tmp_path):
    """覆盖：缓存未命中时返回 None。"""
    db_path = tmp_path / "request_cache.db"
    cache = RequestCache(str(db_path))

    assert cache.get_request_cache("not-exists") is None


def test_request_cache_isolated_by_request_content(tmp_path):
    """覆盖：不同请求内容不会串读缓存结果。"""
    db_path = tmp_path / "request_cache.db"
    cache = RequestCache(str(db_path))

    cache.add_request_cache("request-a", "response-a")
    cache.add_request_cache("request-b", "response-b")

    assert cache.get_request_cache("request-a") == "response-a"
    assert cache.get_request_cache("request-b") == "response-b"
