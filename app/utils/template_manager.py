"""
狼人杀智能体模板管理器

基于Jinja2模板系统，管理狼人杀游戏中所有角色的prompt模板。
支持模板加载、缓存、验证和动态渲染。
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template
from casevo.prompt import PromptFactory


class WerewolfTemplateManager:
    """狼人杀模板管理器"""

    def __init__(self, template_dir: str = "app/prompts", llm=None):
        """
        初始化模板管理器

        Args:
            template_dir: 模板目录路径
            llm: 语言模型实例
        """
        self.template_dir = Path(template_dir)
        self.llm = llm

        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # 模板缓存
        self.template_cache: Dict[str, Template] = {}

        # 如果有LLM，初始化PromptFactory
        if llm:
            self.prompt_factory = PromptFactory(
                tar_folder=str(self.template_dir),
                llm=llm
            )

    def get_template(self, template_path: str) -> Template:
        """
        获取Jinja2模板

        Args:
            template_path: 模板文件路径（相对于template_dir）

        Returns:
            Jinja2模板对象
        """
        # 检查缓存
        if template_path in self.template_cache:
            return self.template_cache[template_path]

        try:
            # 加载模板
            template = self.jinja_env.get_template(template_path)

            # 缓存模板
            self.template_cache[template_path] = template

            return template

        except Exception as e:
            raise ValueError(f"无法加载模板 {template_path}: {str(e)}")

    def render_template(self, template_path: str, **kwargs) -> str:
        """
        渲染模板

        Args:
            template_path: 模板文件路径
            **kwargs: 模板变量

        Returns:
            渲染后的字符串
        """
        template = self.get_template(template_path)

        try:
            return template.render(**kwargs)
        except Exception as e:
            raise ValueError(f"模板渲染失败 {template_path}: {str(e)}")

    def get_werewolf_templates(self) -> Dict[str, str]:
        """
        获取所有狼人角色的模板路径

        Returns:
            模板路径字典
        """
        return {
            "night_action": "werewolf/night_action.j2",
            "day_discussion": "werewolf/day_discussion.j2",
            "defense": "werewolf/defense.j2",
            "voting": "werewolf/voting.j2"
        }

    def get_common_templates(self) -> Dict[str, str]:
        """
        获取通用模板路径

        Returns:
            模板路径字典
        """
        return {
            "role_reveal": "common/role_reveal.j2"
        }

    def render_werewolf_template(self, template_name: str,
                                agent_data: Dict[str, Any],
                                game_data: Dict[str, Any],
                                extra_data: Optional[Dict[str, Any]] = None) -> str:
        """
        渲染狼人角色模板

        Args:
            template_name: 模板名称
            agent_data: 智能体数据
            game_data: 游戏数据
            extra_data: 额外数据

        Returns:
            渲染后的内容
        """
        templates = self.get_werewolf_templates()

        if template_name not in templates:
            raise ValueError(f"未知的狼人模板: {template_name}")

        template_path = templates[template_name]

        # 构建模板变量
        template_vars = {
            "agent": agent_data,
            "game": game_data,
            "extra": extra_data or {}
        }

        return self.render_template(template_path, **template_vars)

    def validate_template_variables(self, template_path: str,
                                  variables: Dict[str, Any]) -> List[str]:
        """
        验证模板所需的变量

        Args:
            template_path: 模板路径
            variables: 提供的变量

        Returns:
            缺失的变量列表
        """
        template = self.get_template(template_path)

        # 获取模板中使用的变量
        template_source = template.source
        required_vars = set()

        # 简单的变量提取（可以根据需要扩展）
        import re
        pattern = r'\{\{\s*([^}]+)\s*\}\}'
        matches = re.findall(pattern, template_source)

        for match in matches:
            # 提取变量名（去掉过滤器等）
            var_name = match.split('.')[0].split('|')[0].strip()
            if var_name:
                required_vars.add(var_name)

        # 检查缺失的变量
        missing_vars = []
        for var in required_vars:
            if var not in variables:
                missing_vars.append(var)

        return missing_vars

    def clear_cache(self):
        """清除模板缓存"""
        self.template_cache.clear()

    def get_template_info(self, template_path: str) -> Dict[str, Any]:
        """
        获取模板信息

        Args:
            template_path: 模板路径

        Returns:
            模板信息字典
        """
        full_path = self.template_dir / template_path

        if not full_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {full_path}")

        stat = full_path.stat()

        return {
            "path": str(full_path),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "exists": True
        }

    def list_templates(self, subdirectory: str = "") -> List[str]:
        """
        列出指定目录下的所有模板文件

        Args:
            subdirectory: 子目录名

        Returns:
            模板文件路径列表
        """
        if subdirectory:
            search_dir = self.template_dir / subdirectory
        else:
            search_dir = self.template_dir

        if not search_dir.exists():
            return []

        templates = []
        for file_path in search_dir.rglob("*.j2"):
            # 获取相对于template_dir的路径
            rel_path = file_path.relative_to(self.template_dir)
            templates.append(str(rel_path))

        return sorted(templates)

    def batch_render(self, template_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量渲染模板

        Args:
            template_configs: 模板配置列表，每个配置包含:
                - template_name: 模板名称
                - agent_data: 智能体数据
                - game_data: 游戏数据
                - extra_data: 额外数据（可选）

        Returns:
            渲染结果列表
        """
        results = []

        for config in template_configs:
            try:
                template_name = config["template_name"]
                agent_data = config["agent_data"]
                game_data = config["game_data"]
                extra_data = config.get("extra_data", {})

                # 根据模板名称确定模板路径
                if template_name in self.get_werewolf_templates():
                    content = self.render_werewolf_template(
                        template_name, agent_data, game_data, extra_data
                    )
                else:
                    # 其他模板的处理
                    template_path = f"{template_name}.j2"
                    template_vars = {
                        "agent": agent_data,
                        "game": game_data,
                        "extra": extra_data
                    }
                    content = self.render_template(template_path, **template_vars)

                results.append({
                    "template_name": template_name,
                    "success": True,
                    "content": content,
                    "error": None
                })

            except Exception as e:
                results.append({
                    "template_name": config.get("template_name", "unknown"),
                    "success": False,
                    "content": None,
                    "error": str(e)
                })

        return results

    def create_agent_template_vars(self, agent_profile: Dict[str, Any],
                                 current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        为智能体创建标准化的模板变量

        Args:
            agent_profile: 智能体人设数据
            current_state: 当前状态数据

        Returns:
            标准化的智能体变量
        """
        return {
            "role": agent_profile["name"],
            "role_id": agent_profile["id"],
            "faction": agent_profile["faction"],
            "description": self._format_description(agent_profile),
            "personality": agent_profile["personality"],
            "objectives": agent_profile["objectives"],
            "abilities": agent_profile["abilities"],
            "decision_weights": agent_profile["decision_weights"],
            "strategies": agent_profile["strategies"],
            **current_state
        }

    def _format_description(self, agent_profile: Dict[str, Any]) -> str:
        """
        格式化智能体描述

        Args:
            agent_profile: 智能体人设数据

        Returns:
            格式化的描述字符串
        """
        parts = []

        # 基本信息
        parts.append(f"角色：{agent_profile['name']}")
        parts.append(f"阵营：{agent_profile['faction']}")
        parts.append(f"胜利条件：{agent_profile['victory_condition']}")

        # 技能
        if agent_profile.get("skills"):
            parts.append("技能：")
            for skill in agent_profile["skills"]:
                parts.append(f"- {skill}")

        # 核心目标
        if agent_profile.get("objectives", {}).get("primary"):
            parts.append("主要目标：")
            for objective in agent_profile["objectives"]["primary"]:
                parts.append(f"- {objective}")

        return "\n".join(parts)


# 便捷函数
def create_werewolf_template_manager(template_dir: str = "app/prompts",
                                   llm=None) -> WerewolfTemplateManager:
    """
    创建狼人杀模板管理器实例

    Args:
        template_dir: 模板目录
        llm: 语言模型实例

    Returns:
        模板管理器实例
    """
    return WerewolfTemplateManager(template_dir, llm)


def render_werewolf_prompt(template_name: str,
                          agent_data: Dict[str, Any],
                          game_data: Dict[str, Any],
                          extra_data: Optional[Dict[str, Any]] = None,
                          template_dir: str = "app/prompts") -> str:
    """
    便捷的狼人模板渲染函数

    Args:
        template_name: 模板名称
        agent_data: 智能体数据
        game_data: 游戏数据
        extra_data: 额外数据
        template_dir: 模板目录

    Returns:
        渲染后的内容
    """
    manager = WerewolfTemplateManager(template_dir)
    return manager.render_werewolf_template(template_name, agent_data, game_data, extra_data)