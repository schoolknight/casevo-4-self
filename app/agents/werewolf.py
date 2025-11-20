"""
狼人杀游戏中的狼人智能体

基于Casevo框架和原生prompt机制实现的狼人AI智能体。
该智能体具备完整的狼人行为逻辑，包括夜晚击杀、白天发言、
投票决策、身份伪装等核心功能。
"""

import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

from casevo import AgentBase
from casevo.chain import BaseStep, JsonStep, ChoiceStep, ScoreStep


class WerewolfAgent(AgentBase):
    """
    狼人杀游戏中的狼人智能体

    继承自Casevo的AgentBase，专注于狼人角色的完整AI实现。
    使用Casevo原生prompt机制，支持复杂的决策逻辑和角色扮演。
    """

    def __init__(self, unique_id: int, model, role_data: Dict[str, Any], context: Optional[Dict] = None):
        """
        初始化狼人智能体

        Args:
            unique_id: 智能体唯一标识
            model: 游戏模型实例
            role_data: 角色人设数据
            context: 游戏上下文
        """
        # 生成标准智能体描述（符合Casevo格式）
        description = self._create_agent_description(role_data)

        # 生成智能体上下文（存储游戏状态）
        agent_context = {
            "role_data": role_data,
            "game_state": {
                "is_alive": True,
                "fake_role": "civilian",  # 伪装身份
                "suspicion_level": 0.0,  # 被怀疑程度
                "teammates": [],  # 狼队友列表
                "last_kill_target": None,  # 上次击杀目标
                "night_actions": [],  # 夜晚行动记录
                "day_statements": [],  # 白天发言记录
                "vote_history": []  # 投票历史
            }
        }

        if context:
            agent_context.update(context)

        # 调用父类初始化
        super().__init__(unique_id, model, description, agent_context)

        # 角色相关属性（从context中获取）
        self.role_data = role_data
        self.role_name = role_data["name"]
        self.role_id = role_data["id"]
        self.faction = role_data["faction"]

        # 设置思维链（使用标准prompt模板）
        self.setup_werewolf_chains()

    def _create_agent_description(self, role_data: Dict[str, Any]) -> Dict[str, str]:
        """创建符合Casevo标准的智能体描述"""
        return {
            "general": f"你是狼人杀游戏中的{role_data['name']}，阵营：{role_data['faction']}",
            "character": self._format_character_traits(role_data),
            "issue": self._format_objectives(role_data)
        }

    def _format_character_traits(self, role_data: Dict[str, Any]) -> str:
        """格式化性格特征"""
        traits = []

        # 基本信息
        traits.append(f"胜利条件：{role_data['victory_condition']}")

        # 技能
        if role_data.get("skills"):
            traits.append("技能：")
            for skill in role_data["skills"]:
                traits.append(f"- {skill}")

        # 核心特征
        if "personality" in role_data and "core" in role_data["personality"]:
            traits.append("核心特征：")
            for trait in role_data["personality"]["core"]:
                traits.append(f"- {trait}")

        # 发言风格
        if "personality" in role_data and "speaking_style" in role_data["personality"]:
            traits.append("发言风格：")
            for style in role_data["personality"]["speaking_style"]:
                traits.append(f"- {style}")

        return "\n".join(traits)

    def _format_objectives(self, role_data: Dict[str, Any]) -> str:
        """格式化目标和倾向"""
        objectives = []

        # 主要目标
        if "objectives" in role_data and "primary" in role_data["objectives"]:
            objectives.append("主要目标：")
            for obj in role_data["objectives"]["primary"]:
                objectives.append(f"- {obj}")

        # 次要目标
        if "objectives" in role_data and "secondary" in role_data["objectives"]:
            objectives.append("次要目标：")
            for obj in role_data["objectives"]["secondary"]:
                objectives.append(f"- {obj}")

        return "\n".join(objectives)

    def setup_werewolf_chains(self):
        """设置狼人专用思维链（使用Casevo标准模式）"""

        # 加载prompt模板
        night_kill_prompt = self.model.prompt_factory.get_template("werewolf/night_action.txt")
        day_discussion_prompt = self.model.prompt_factory.get_template("werewolf/day_discussion.txt")
        defense_prompt = self.model.prompt_factory.get_template("werewolf/defense.txt")
        voting_prompt = self.model.prompt_factory.get_template("werewolf/voting.txt")
        reflect_prompt = self.model.prompt_factory.get_template("werewolf/reflect.txt")

        # 定义自定义步骤类（参考election_agent.py）
        class NightKillStep(JsonStep):
            def pre_process(self, input, agent=None, model=None):
                cur_input = input['input']
                cur_input['agent_state'] = agent.context["game_state"] if agent else {}
                cur_input['phase'] = cur_input.get('phase', 1)
                return cur_input

        class DayDiscussionStep(BaseStep):
            def pre_process(self, input, agent=None, model=None):
                cur_input = input['input']
                cur_input['previous_statements'] = agent.context["game_state"]["day_statements"][-3:] if agent else []
                cur_input['phase_name'] = cur_input.get('phase_name', '白天')
                cur_input['speak_order'] = cur_input.get('speak_order', 1)
                return cur_input

        class DefenseStep(BaseStep):
            def pre_process(self, input, agent=None, model=None):
                cur_input = input['input']
                cur_input['accusations'] = input.get('accusations', [])
                cur_input['suspicion_level'] = agent.context["game_state"]["suspicion_level"] if agent else 0.0
                return cur_input

        class VotingStep(JsonStep):
            def pre_process(self, input, agent=None, model=None):
                cur_input = input['input']
                cur_input['vote_history'] = agent.context["game_state"]["vote_history"][-5:] if agent else []
                cur_input['voting_round'] = cur_input.get('voting_round', 1)
                return cur_input

        class ReflectStep(BaseStep):
            def pre_process(self, input, agent=None, model=None):
                cur_input = input['input']
                cur_input['round_performance'] = input.get('round_performance', {})
                cur_input['team_performance'] = input.get('team_performance', {})
                cur_input['teammate_performance'] = input.get('teammate_performance', [])
                return cur_input

        # 设置思维链
        night_kill_step = NightKillStep(0, night_kill_prompt)
        day_discussion_step = DayDiscussionStep(0, day_discussion_prompt)
        defense_step = DefenseStep(0, defense_prompt)
        voting_step = VotingStep(0, voting_prompt)
        reflect_step = ReflectStep(0, reflect_prompt)

        chain_dict = {
            'night_kill': [night_kill_step],
            'day_discussion': [day_discussion_step],
            'defense': [defense_step],
            'voting': [voting_step],
            'reflect': [reflect_step]
        }

        self.setup_chain(chain_dict)

    def get_agent_state(self) -> Dict[str, Any]:
        """获取智能体当前状态"""
        return {
            "role": self.role_name,
            "role_id": self.role_id,
            "faction": self.faction,
            "is_alive": self.is_alive,
            "fake_role": self.fake_role,
            "suspicion_level": self.suspicion_level,
            "teammates": self.teammates,
            "night_actions": self.night_actions,
            "day_statements": self.day_statements,
            "vote_history": self.vote_history,
            "last_kill_target": self.last_kill_target,
            "total_votes": len(self.vote_history),
            "vote_accuracy": self._calculate_vote_accuracy()
        }

    def night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        狼人夜晚行动：选择击杀目标（使用Casevo标准模式）

        Args:
            game_state: 当前游戏状态

        Returns:
            击杀决策结果
        """
        if not self.context["game_state"]["is_alive"]:
            return {"action": "none", "reason": "已死亡"}

        # 准备思维链输入数据
        input_item = {
            "phase": game_state.get("phase", 1),
            "potential_victims": game_state.get("potential_victims", []),
            "teammates": self.context["game_state"]["teammates"],
            "previous_kills": self.context["game_state"]["night_actions"],
            "last_night_result": game_state.get("last_night_result"),
            "kill_succeeded": game_state.get("kill_succeeded", False),
            "teammate_suggestions": game_state.get("teammate_suggestions", []),
            "important_info": game_state.get("important_info", []),
            "can_self_kill": game_state.get("can_self_kill", False)
        }

        # 设置思维链输入并运行
        self.chains['night_kill'].set_input(input_item)

        try:
            self.chains['night_kill'].run_step()

            # 获取结果
            result = self.chains['night_kill'].get_output()

            # 解析JSON决策
            if 'json' in result:
                decision = result['json']
            else:
                decision = {"target_id": None, "reason": "无法解析决策"}

            # 记录行动
            action_record = {
                "round": game_state.get("phase", 1),
                "target_id": decision.get("target_id"),
                "reason": decision.get("reason", "未提供理由"),
                "timestamp": datetime.now().isoformat()
            }
            self.context["game_state"]["night_actions"].append(action_record)
            self.context["game_state"]["last_kill_target"] = decision.get("target_id")

            return {
                "action": "kill",
                "target": decision.get("target_id"),
                "reason": decision.get("reason", "未提供理由"),
                "success": True
            }

        except Exception as e:
            # 错误处理：随机选择目标
            available_targets = game_state.get("potential_victims", [])
            if available_targets:
                target = random.choice(available_targets)["id"]
                return {
                    "action": "kill",
                    "target": target,
                    "reason": f"决策出错，随机选择目标。错误：{str(e)}",
                    "success": False
                }
            else:
                return {
                    "action": "none",
                    "reason": f"无可击杀目标。错误：{str(e)}",
                    "success": False
                }

    def day_discussion(self, game_state: Dict[str, Any],
                      context: Optional[Dict] = None) -> str:
        """
        白天讨论发言（使用Casevo标准模式）

        Args:
            game_state: 游戏状态
            context: 额外上下文

        Returns:
            发言内容
        """
        if not self.context["game_state"]["is_alive"]:
            return "（已死亡）"

        # 准备思维链输入数据
        input_item = {
            "phase": game_state.get("phase", 1),
            "phase_name": game_state.get("phase_name", "白天"),
            "last_night_result": game_state.get("last_night_result"),
            "already_spoken": game_state.get("already_spoken", []),
            "urgent_situation": game_state.get("urgent_situation"),
            "player_suspicions": game_state.get("player_suspicions", {}),
            "team_strategy": context.get("team_strategy") if context else None,
            "speak_order": game_state.get("speak_order", 1),
            "alive_count": game_state.get("alive_count", 0)
        }

        # 设置思维链输入并运行
        self.chains['day_discussion'].set_input(input_item)

        try:
            self.chains['day_discussion'].run_step()

            # 获取结果
            result = self.chains['day_discussion'].get_output()
            response = result.get('last_response', "我认为需要仔细分析当前局势。")

            # 记录发言
            statement = {
                "round": game_state.get("phase", 1),
                "content": response,
                "type": "discussion",
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            self.context["game_state"]["day_statements"].append(statement)

            return response

        except Exception as e:
            # 错误处理：通用发言
            default_response = f"我认为需要仔细分析当前局势，找出真正的狼人。暂时没有具体的怀疑对象。"
            statement = {
                "round": game_state.get("phase", 1),
                "content": default_response,
                "type": "discussion",
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            self.context["game_state"]["day_statements"].append(statement)
            return default_response

    def defense(self, accusations: List[Dict[str, Any]],
               game_state: Dict[str, Any]) -> str:
        """
        辩护发言（使用Casevo标准模式）

        Args:
            accusations: 指控列表
            game_state: 游戏状态

        Returns:
            辩护发言内容
        """
        if not self.context["game_state"]["is_alive"]:
            return "（已死亡）"

        # 更新被怀疑程度
        current_suspicion = self.context["game_state"]["suspicion_level"]
        self.context["game_state"]["suspicion_level"] = min(current_suspicion + 0.2, 1.0)

        # 准备思维链输入数据
        input_item = {
            "accusations": accusations,
            "accusers": list(set(acc["accuser_id"] for acc in accusations)),
            "vote_risk": "high" if len(accusations) > 2 else "medium",
            "main_accuser": accusations[0]["accuser_id"] if accusations else None
        }

        # 设置思维链输入并运行
        self.chains['defense'].set_input(input_item)

        try:
            self.chains['defense'].run_step()

            # 获取结果
            result = self.chains['defense'].get_output()
            response = result.get('last_response', "我是好人，请大家相信我。")

            # 记录辩护
            statement = {
                "type": "defense",
                "round": game_state.get("phase", 1),
                "content": response,
                "accusations": accusations,
                "timestamp": datetime.now().isoformat()
            }
            self.context["game_state"]["day_statements"].append(statement)

            return response

        except Exception as e:
            default_response = "我是好人，请大家相信我。那些指控都是没有根据的。"
            statement = {
                "type": "defense",
                "round": game_state.get("phase", 1),
                "content": default_response,
                "accusations": accusations,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            self.context["game_state"]["day_statements"].append(statement)
            return default_response

    def vote(self, candidates: List[Dict[str, Any]],
            game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        投票决策（使用Casevo标准模式）

        Args:
            candidates: 候选人列表
            game_state: 游戏状态

        Returns:
            投票决策
        """
        if not self.context["game_state"]["is_alive"]:
            return {"vote_target": None, "reason": "已死亡"}

        # 准备思维链输入数据
        input_item = {
            "candidates": candidates,
            "voting_reason": game_state.get("voting_reason", "常规投票"),
            "voting_round": game_state.get("voting_round", 1),
            "urgent_vote": game_state.get("urgent_vote", False),
            "werewolf_advantage": game_state.get("werewolf_advantage", False),
            "team_coordination": self._get_team_voting_plan(candidates)
        }

        # 设置思维链输入并运行
        self.chains['voting'].set_input(input_item)

        try:
            self.chains['voting'].run_step()

            # 获取结果
            result = self.chains['voting'].get_output()

            # 解析投票决策
            if 'json' in result:
                decision = result['json']
            else:
                decision = {"vote_target": None, "primary_reason": "无法解析决策"}

            # 获取投票目标
            vote_target = decision.get("vote_target")
            if not vote_target and candidates:
                # 如果没有明确目标，选择最可疑的
                vote_target = min(candidates,
                                key=lambda x: x.get("suspicion_level", 0)).get("id")

            # 记录投票
            vote_record = {
                "round": game_state.get("phase", 1),
                "target_id": vote_target,
                "reason": decision.get("primary_reason", "基于当前局势的分析"),
                "candidates": [c["id"] for c in candidates],
                "timestamp": datetime.now().isoformat()
            }
            self.context["game_state"]["vote_history"].append(vote_record)

            return {
                "vote_target": vote_target,
                "reason": decision.get("primary_reason", "基于当前局势的分析"),
                "confidence": decision.get("risk_assessment", {}).get("success_probability", 0.5)
            }

        except Exception as e:
            # 错误处理：随机投票
            if candidates:
                target = random.choice(candidates)["id"]
                return {
                    "vote_target": target,
                    "reason": f"决策出错，随机投票。错误：{str(e)}",
                    "confidence": 0.3
                }
            else:
                return {
                    "vote_target": None,
                    "reason": f"无可投票候选人。错误：{str(e)}",
                    "confidence": 0.0
                }

    def update_suspicion(self, new_level: float):
        """更新被怀疑程度"""
        self.context["game_state"]["suspicion_level"] = max(0.0, min(1.0, new_level))

    def set_fake_role(self, fake_role: str, fake_description: str = ""):
        """设置伪装身份"""
        self.context["game_state"]["fake_role"] = fake_role
        if fake_description:
            self.context["game_state"]["fake_role_description"] = fake_description

    def add_teammate(self, teammate_id: int, teammate_info: Dict[str, Any]):
        """添加狼队友"""
        if teammate_id not in [t["id"] for t in self.context["game_state"]["teammates"]]:
            self.context["game_state"]["teammates"].append({
                "id": teammate_id,
                **teammate_info
            })

    def get_agent_state(self) -> Dict[str, Any]:
        """获取智能体当前状态"""
        return {
            "role": self.role_name,
            "role_id": self.role_id,
            "faction": self.faction,
            "is_alive": self.context["game_state"]["is_alive"],
            "fake_role": self.context["game_state"]["fake_role"],
            "suspicion_level": self.context["game_state"]["suspicion_level"],
            "teammates": self.context["game_state"]["teammates"],
            "night_actions": self.context["game_state"]["night_actions"],
            "day_statements": self.context["game_state"]["day_statements"],
            "vote_history": self.context["game_state"]["vote_history"],
            "last_kill_target": self.context["game_state"]["last_kill_target"],
            "total_votes": len(self.context["game_state"]["vote_history"]),
            "vote_accuracy": self._calculate_vote_accuracy()
        }

    def _get_team_voting_plan(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取团队投票计划"""
        # 检查是否有队友在候选人中
        teammate_ids = [t["id"] for t in self.context["game_state"]["teammates"]]
        teammates_in_candidates = [c for c in candidates if c["id"] in teammate_ids]

        if teammates_in_candidates:
            return {
                "primary_target": None,  # 保护队友，不投队友
                "split_votes": "avoid_teammates",
                "backup_plan": "vote_least_suspicious_non_teammate"
            }
        else:
            return {
                "primary_target": "most_suspicious_candidate",
                "split_votes": "coordinate_on_main_target",
                "backup_plan": "coordinate_on_secondary_target"
            }

    def _calculate_vote_accuracy(self) -> float:
        """计算投票准确率"""
        vote_history = self.context["game_state"]["vote_history"]
        if not vote_history:
            return 0.0

        correct_votes = sum(1 for vote in vote_history
                           if vote.get("correct", False))
        return correct_votes / len(vote_history)

    def reflect(self):
        """反思和学习（使用Casevo标准模式）"""
        if not self.context["game_state"]["is_alive"]:
            return

        # 准备反思思维链输入数据
        round_performance = {
            "actions": self.context["game_state"]["night_actions"][-1:] if self.context["game_state"]["night_actions"] else [],
            "speeches": self.context["game_state"]["day_statements"][-3:] if self.context["game_state"]["day_statements"] else []
        }

        input_item = {
            "phase": getattr(getattr(self.model, 'schedule', None), 'time', 1),
            "suspicion_level": self.context["game_state"]["suspicion_level"],
            "team_status": self._get_team_status(),
            "problems": self._identify_problems(),
            "successes": self._identify_successes(),
            "failures": self._identify_failures(),
            "short_term_goals": self._get_short_term_goals(),
            "medium_term_goals": self._get_medium_term_goals()
        }

        # 设置思维链输入并运行
        self.chains['reflect'].set_input(input_item)

        try:
            self.chains['reflect'].run_step()

            # 获取反思结果
            result = self.chains['reflect'].get_output()

            # 记录反思结果
            reflection = {
                "round": input_item.get("phase", 0),
                "performance_summary": result.get('json', {}).get("performance_summary", {}),
                "strategy_adjustments": result.get('json', {}).get("strategy_adjustments", []),
                "skill_development": result.get('json', {}).get("skill_development", {}),
                "next_phase_planning": result.get('json', {}).get("next_phase_planning", {}),
                "timestamp": datetime.now().isoformat()
            }

            # 添加到记忆
            self.memory.add_short_memory(
                "reflection", self.component_id, "werewolf_reflection",
                json.dumps(reflection, ensure_ascii=False)
            )

            # 根据反思结果调整策略
            self._apply_reflection_adjustments(result.get('json', {}))

        except Exception as e:
            # 错误处理
            basic_reflection = {
                "round": input_item.get("phase", 0),
                "performance_summary": {"overall_rating": "需改进"},
                "strategy_adjustments": ["加强分析能力"],
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            self.memory.add_short_memory(
                "reflection", self.component_id, "werewolf_reflection",
                json.dumps(basic_reflection, ensure_ascii=False)
            )

    def _get_team_status(self) -> str:
        """获取团队状况"""
        teammate_count = len(self.context["game_state"]["teammates"])
        if teammate_count == 0:
            return "未知队友信息"
        elif teammate_count == 1:
            return f"与1名队友协作"
        else:
            return f"与{teammate_count}名队友协作"

    def _identify_problems(self) -> List[Dict[str, Any]]:
        """识别问题"""
        problems = []

        if self.context["game_state"]["suspicion_level"] > 0.7:
            problems.append({
                "type": "高度怀疑",
                "description": f"被怀疑程度过高({self.context['game_state']['suspicion_level']})",
                "severity": "高",
                "impact": "生存威胁",
                "urgency": "立即"
            })

        return problems

    def _identify_successes(self) -> List[Dict[str, Any]]:
        """识别成功经验"""
        successes = []

        if self.context["game_state"]["night_actions"]:
            successful_kills = len([a for a in self.context["game_state"]["night_actions"] if a.get("success", False)])
            if successful_kills > 0:
                successes.append({
                    "experience": "成功击杀目标",
                    "method": "威胁分析和目标选择",
                    "applicability": "可复用",
                    "replicability": "高"
                })

        return successes

    def _identify_failures(self) -> List[Dict[str, Any]]:
        """识别失败教训"""
        failures = []

        return failures

    def _get_short_term_goals(self) -> List[Dict[str, Any]]:
        """获取短期目标"""
        goals = []
        if self.context["game_state"]["suspicion_level"] > 0.5:
            goals.append({
                "description": "降低被怀疑程度",
                "action_plan": "改善发言质量和伪装技巧",
                "success_criteria": "被怀疑度降低到0.3以下",
                "timeline": "1-2轮"
            })
        return goals

    def _get_medium_term_goals(self) -> List[Dict[str, Any]]:
        """获取中期目标"""
        goals = []
        goals.append({
            "description": "提高伪装技能",
            "action_plan": "学习和模仿不同角色的发言模式",
            "success_criteria": "成功伪装不暴露身份",
            "timeline": "3-5轮"
        })
        return goals

    def _apply_reflection_adjustments(self, reflection_result: Dict[str, Any]):
        """应用反思调整"""
        # 可以根据反思结果调整策略参数
        pass

    def step(self):
        """执行一步操作（由框架调用）"""
        if not self.context["game_state"]["is_alive"]:
            return

        # 获取当前游戏状态
        game_state = self._get_current_game_state()

        if not game_state:
            return

        # 根据游戏阶段执行相应行动
        phase = game_state.get("phase", "day")

        if phase == "night":
            # 夜晚行动
            self.night_action(game_state)
        elif phase == "day":
            # 白天行动
            context = game_state.get("context")
            self.day_discussion(game_state, context)

        # 反思
        self.reflect()

    def _get_current_game_state(self) -> Optional[Dict[str, Any]]:
        """获取当前游戏状态"""
        # 这里需要从模型中获取游戏状态
        # 具体实现取决于游戏模型的接口
        if hasattr(self.model, 'get_game_state'):
            return self.model.get_game_state()
        elif hasattr(self.model, 'game_state'):
            return self.model.game_state
        else:
            return None


def create_werewolf_agent(unique_id: int, model, role_data: Dict[str, Any],
                         context: Optional[Dict] = None) -> WerewolfAgent:
    """
    创建狼人智能体实例

    Args:
        unique_id: 唯一标识
        model: 游戏模型
        role_data: 角色人设数据
        context: 上下文

    Returns:
        狼人智能体实例
    """
    return WerewolfAgent(unique_id, model, role_data, context)