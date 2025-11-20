"""
狼人杀智能体模块

包含各种角色的智能体实现，基于Casevo框架和Jinja2模板系统。
"""

from .werewolf import WerewolfAgent, create_werewolf_agent

__all__ = [
    "WerewolfAgent",
    "create_werewolf_agent"
]