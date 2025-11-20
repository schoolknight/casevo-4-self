"""
狼人智能体使用示例

演示如何创建和使用狼人智能体。
"""

import json
from pathlib import Path

from app.agents.werewolf import create_werewolf_agent
from app.utils.template_manager import WerewolfTemplateManager


def load_role_data():
    """加载角色人设数据"""
    profile_path = Path(".claude/doc/profile/person.json")

    if not profile_path.exists():
        raise FileNotFoundError(f"角色人设文件不存在: {profile_path}")

    with open(profile_path, 'r', encoding='utf-8') as f:
        roles = json.load(f)

    # 查找狼人角色数据
    for role in roles:
        if role['id'] == 'werewolf':
            return role

    raise ValueError("未找到狼人角色数据")


def create_sample_game_state():
    """创建示例游戏状态"""
    return {
        "phase": 1,
        "phase_name": "第一夜",
        "alive_count": 6,
        "alive_players": [
            {"id": 1, "suspicion_level": 0.2},
            {"id": 2, "suspicion_level": 0.8},
            {"id": 3, "suspicion_level": 0.4},
            {"id": 4, "suspicion_level": 0.1},
            {"id": 5, "suspicion_level": 0.6},
            {"id": 6, "suspicion_level": 0.3}
        ],
        "potential_victims": [
            {
                "id": 2,
                "threat_level": "high",
                "role_probability": {"werewolf": 0.1, "good": 0.9},
                "suspicious_behaviors": [
                    {"description": "发言逻辑性强", "confidence": 0.8}
                ]
            },
            {
                "id": 5,
                "threat_level": "medium",
                "role_probability": {"werewolf": 0.2, "good": 0.8},
                "suspicious_behaviors": []
            }
        ]
    }


def create_sample_day_game_state():
    """创建示例白天游戏状态"""
    return {
        "phase": 1,
        "phase_name": "第一天白天",
        "alive_count": 5,  # 假设昨晚有人死亡
        "last_night_result": "昨晚2号玩家被击杀",
        "already_spoken": [
            {
                "player_id": 3,
                "content": "我认为我们需要找出谁是狼人。",
                "suspicion_indicators": []
            },
            {
                "player_id": 4,
                "content": "2号的死很可疑，大家要小心。",
                "suspicion_indicators": [
                    {"description": "转移话题", "severity": "medium"}
                ]
            }
        ],
        "player_suspicions": {
            1: {"suspicion_level": 0.2, "main_suspicion": "表现正常"},
            3: {"suspicion_level": 0.3, "main_suspicion": "发言普通"},
            4: {"suspicion_level": 0.6, "main_suspicion": "发言可疑"},
            5: {"suspicion_level": 0.4, "main_suspicion": "行为异常"},
            6: {"suspicion_level": 0.3, "main_suspicion": "沉默寡言"}
        }
    }


def example_night_action():
    """夜晚行动示例"""
    print("=== 狼人夜晚行动示例 ===")

    # 加载角色数据
    role_data = load_role_data()

    # 创建模拟模型（这里简化处理）
    class MockModel:
        def get_game_state(self):
            return create_sample_game_state()

    mock_model = MockModel()

    # 创建狼人智能体
    werewolf = create_werewolf_agent(
        unique_id=1,
        model=mock_model,
        role_data=role_data
    )

    # 设置伪装身份
    werewolf.set_fake_role("civilian", "普通村民，想找出狼人")

    # 添加狼队友
    werewolf.add_teammate(3, {"suspicion_level": 0.3})

    # 执行夜晚行动
    game_state = create_sample_game_state()
    result = werewolf.night_action(game_state)

    print(f"夜晚行动结果: {result}")
    print(f"选择的击杀目标: {result.get('target')}")
    print(f"行动理由: {result.get('reason')}")
    print()


def example_day_discussion():
    """白天讨论示例"""
    print("=== 狼人白天讨论示例 ===")

    # 加载角色数据
    role_data = load_role_data()

    # 创建模拟模型
    class MockModel:
        def get_game_state(self):
            return create_sample_day_game_state()

    mock_model = MockModel()

    # 创建狼人智能体
    werewolf = create_werewolf_agent(
        unique_id=1,
        model=mock_model,
        role_data=role_data
    )

    # 设置伪装身份
    werewolf.set_fake_role("civilian", "关心游戏进展的村民")

    # 执行白天讨论
    game_state = create_sample_day_game_state()
    statement = werewolf.day_discussion(game_state)

    print(f"白天发言内容:")
    print(statement)
    print()


def example_template_usage():
    """模板使用示例"""
    print("=== 模板系统使用示例 ===")

    # 创建模板管理器
    template_manager = WerewolfTemplateManager()

    # 准备示例数据
    agent_data = {
        "role": "狼人",
        "role_id": "werewolf",
        "faction": "狼人阵营",
        "fake_role": "civilian",
        "teammates": [{"id": 3, "suspicion_level": 0.3}],
        "suspicion_level": 0.2
    }

    game_state = create_sample_game_state()

    extra_data = {
        "last_night_result": "平安夜",
        "memory": []
    }

    # 渲染夜晚击杀模板
    try:
        prompt = template_manager.render_werewolf_template(
            "night_action",
            agent_data,
            game_state,
            extra_data
        )

        print("夜晚击杀模板渲染成功!")
        print(f"模板长度: {len(prompt)} 字符")
        print("模板内容（前200字符）:")
        print(prompt[:200] + "...")

    except Exception as e:
        print(f"模板渲染失败: {e}")

    print()


def example_vote_decision():
    """投票决策示例"""
    print("=== 狼人投票决策示例 ===")

    # 加载角色数据
    role_data = load_role_data()

    # 创建模拟模型
    class MockModel:
        def get_game_state(self):
            return create_sample_day_game_state()

    mock_model = MockModel()

    # 创建狼人智能体
    werewolf = create_werewolf_agent(
        unique_id=1,
        model=mock_model,
        role_data=role_data
    )

    # 准备候选人
    candidates = [
        {"id": 3, "suspicion_level": 0.3},
        {"id": 4, "suspicion_level": 0.6},
        {"id": 5, "suspicion_level": 0.4}
    ]

    # 执行投票决策
    game_state = create_sample_day_game_state()
    vote_result = werewolf.vote(candidates, game_state)

    print(f"投票目标: {vote_result.get('vote_target')}")
    print(f"投票理由: {vote_result.get('reason')}")
    print(f"投票置信度: {vote_result.get('confidence')}")
    print()


def main():
    """主函数 - 运行所有示例"""
    print("狼人智能体使用示例")
    print("=" * 50)

    try:
        example_template_usage()
        example_night_action()
        example_day_discussion()
        example_vote_decision()

    except Exception as e:
        print(f"示例运行出错: {e}")
        print("请确保:")
        print("1. .claude/doc/profile/person.json 文件存在")
        print("2. app/prompts/ 目录下的模板文件存在")
        print("3. 相关依赖已正确安装")


if __name__ == "__main__":
    main()