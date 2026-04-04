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
