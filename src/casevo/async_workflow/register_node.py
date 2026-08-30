"""⚠️ DEPRECATED (2026-08-30)：本模块将由 Flovo 引擎（https://github.com/rgCASS/Flovo）
取代。请通过 casevo.flovo_client.FlovoClient 接入（见 examples/flovo_integration/）。
不再新增功能，仅修复致命 Bug。"""

from __future__ import annotations

from typing import Callable, Optional, Union


# 注册节点类装饰器，支持类名 + 别名。
def register_class(alias: Optional[Union[str, list[str]]] = None) -> Callable:
    def decorator(cls):
        names = [cls.__name__]

        if alias:
            if isinstance(alias, str):
                names.append(alias)
            else:
                names.extend(alias)

        cls._alias = names
        cls._decorated_by_register_class = True
        return cls

    return decorator
