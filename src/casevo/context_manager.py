from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any, Dict, List, Optional


class ContextManager:
    """线程安全的上下文管理器。"""

    def __init__(self, initial_context: Optional[Dict] = None):
        # 使用可重入锁，支持同线程内嵌套调用。
        self._lock = RLock()
        self._context: Dict[str, Any] = deepcopy(initial_context) if initial_context else {}

    def get(self) -> Dict:
        """返回上下文副本，避免外部直接改写内部状态。"""
        with self._lock:
            return deepcopy(self._context)

    def to_dict(self) -> Dict:
        """与 get 语义一致，提供更直观的方法名。"""
        return self.get()

    def update(self, updates: Dict) -> None:
        """浅层部分更新：仅覆盖顶层给定字段。"""
        if not isinstance(updates, dict):
            raise TypeError("updates must be a dict")
        with self._lock:
            for key, value in updates.items():
                self._context[key] = deepcopy(value)

    def merge(self, new_context: Dict) -> None:
        """深度合并：对 dict 字段递归合并，其他类型直接覆盖。"""
        if not isinstance(new_context, dict):
            raise TypeError("new_context must be a dict")
        with self._lock:
            self._context = self._deep_merge_dict(self._context, new_context)

    def get_nested(self, path: str, default: Any = None) -> Any:
        """按点分路径读取嵌套字段，不存在时返回 default。"""
        keys = self._parse_path(path)
        with self._lock:
            current: Any = self._context
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    return default
                current = current[key]
            return deepcopy(current)

    def set_nested(self, path: str, value: Any) -> None:
        """按点分路径设置嵌套字段，不存在的中间层会自动创建。"""
        keys = self._parse_path(path)
        with self._lock:
            current = self._context
            for key in keys[:-1]:
                node = current.get(key)
                if not isinstance(node, dict):
                    node = {}
                    current[key] = node
                current = node
            current[keys[-1]] = deepcopy(value)

    def delete(self, keys: List[str]) -> None:
        """批量删除顶层字段；不存在的键会被忽略。"""
        with self._lock:
            for key in keys:
                self._context.pop(key, None)

    def clear(self) -> None:
        """清空上下文。"""
        with self._lock:
            self._context.clear()

    @staticmethod
    def _parse_path(path: str) -> List[str]:
        if not isinstance(path, str) or not path.strip():
            raise ValueError("path must be a non-empty string")
        keys = [item.strip() for item in path.split(".") if item.strip()]
        if not keys:
            raise ValueError("path must contain at least one key")
        return keys

    @classmethod
    def _deep_merge_dict(cls, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        merged = deepcopy(base)
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = cls._deep_merge_dict(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged
