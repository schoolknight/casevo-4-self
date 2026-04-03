"""util/random_name.py 模块单元测试。"""

from __future__ import annotations

from casevo.util.random_name import (
    random_chinese_name,
    random_four_name,
    random_three_name,
    random_three_names,
    random_two_name,
)


def test_random_two_name_returns_two_chars():
    """覆盖：两字姓名生成结果为字符串且长度为 2。"""
    name = random_two_name()
    assert isinstance(name, str)
    assert len(name) == 2


def test_random_three_name_returns_three_chars():
    """覆盖：三字普通姓名长度。"""
    name = random_three_name()
    assert isinstance(name, str)
    assert len(name) == 3


def test_random_three_names_returns_three_chars():
    """覆盖：三字复姓姓名长度。"""
    name = random_three_names()
    assert isinstance(name, str)
    assert len(name) == 3


def test_random_four_name_returns_four_chars():
    """覆盖：四字复姓姓名长度。"""
    name = random_four_name()
    assert isinstance(name, str)
    assert len(name) == 4


def test_random_chinese_name_length_range():
    """覆盖：总入口姓名生成长度范围（2/3/4 字）。"""
    lengths = {len(random_chinese_name()) for _ in range(100)}
    assert lengths.issubset({2, 3, 4})
