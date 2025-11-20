#!/usr/bin/env python3
"""
测试 werewolf.py 智能体的功能
验证所有prompt模板是否能正确加载和执行
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 导入必要的模块
try:
    from casevo import ModelBase
    from casevo.prompt import PromptFactory
    from casevo.chain import JsonStep
    from app.agents.werewolf import WerewolfAgent
    print("✅ 导入模块成功")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)


class MockLLM:
    """模拟 LLM 用于测试"""
    def __send_message__(self, prompt):
        """模拟发送消息并返回简单的JSON响应"""
        return {
            "choices": [{
                "message": {
                    "content": '{"test": "response"}'
                }
            }]
        }


class MockMemory:
    """模拟内存对象"""
    def __init__(self, agent):
        self.agent = agent
        self._data = {}

    def add(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def add_short_memory(self, key, component_id, tag, content):
        """添加短期记忆"""
        self._data[f"short_{key}"] = {
            "key": key,
            "component_id": component_id,
            "tag": tag,
            "content": content
        }

    def add_long_memory(self, content):
        """添加长期记忆"""
        self._data["long_memory"] = self._data.get("long_memory", []) + [content]


class MockMemoryFactory:
    """模拟内存工厂"""
    def __init__(self, llm, memory_num, reflect_prompt, model, memory_path):
        self.llm = llm
        self.memory_num = memory_num
        self.reflect_prompt = reflect_prompt
        self.model = model
        self.memory_path = memory_path

    def create_memory(self, agent):
        return MockMemory(agent)


class MockModel:
    """模拟 ModelBase 用于测试"""
    def __init__(self):
        # 创建模拟的LLM
        self.llm = MockLLM()

        # 设置prompts目录
        prompts_dir = Path(__file__).parent / "prompts"

        # 初始化PromptFactory
        try:
            self.prompt_factory = PromptFactory(str(prompts_dir), self.llm)
            print(f"📂 PromptFactory初始化成功，模板目录: {prompts_dir}")
        except Exception as e:
            print(f"❌ PromptFactory初始化失败: {e}")
            raise

        # 创建反射prompt（需要Mock对象）
        class MockPrompt:
            def send_prompt(self, **kwargs):
                return "模拟的反思响应"

        # 初始化MemoryFactory
        reflect_prompt = MockPrompt()
        self.memory_factory = MockMemoryFactory(
            self.llm, 10, reflect_prompt, self, None
        )

        # 模拟 Mesa Model 的基本属性
        self.context = {}
        self.running = True
        self._agents = []

        # 模拟 ModelBase 的其他属性
        self.agent_list = []
        self.schedule = None
        self.grid = None

    def register_agent(self, agent):
        """注册智能体到模型"""
        if agent not in self._agents:
            self._agents.append(agent)

    def remove_agent(self, agent):
        """从模型中移除智能体"""
        if agent in self._agents:
            self._agents.remove(agent)


def load_test_role_data():
    """加载测试用的角色数据"""
    role_file = Path(__file__).parent.parent / ".claude" / "doc" / "profile" / "person.json"

    if not role_file.exists():
        print(f"❌ 角色数据文件不存在: {role_file}")
        return None

    try:
        with open(role_file, 'r', encoding='utf-8') as f:
            roles = json.load(f)

        # 找到狼人角色数据
        werewolf_data = None
        for role in roles:
            if role['id'] == 'werewolf':
                werewolf_data = role
                break

        if not werewolf_data:
            print("❌ 未找到狼人角色数据")
            return None

        print("✅ 成功加载狼人角色数据")
        return werewolf_data

    except Exception as e:
        print(f"❌ 加载角色数据失败: {e}")
        return None


def test_agent_creation():
    """测试智能体创建"""
    print("\n" + "="*50)
    print("🧪 测试1: 智能体创建")
    print("="*50)

    # 加载角色数据
    role_data = load_test_role_data()
    if not role_data:
        return False

    # 创建模拟模型
    model = MockModel()

    try:
        # 创建智能体
        agent = WerewolfAgent(unique_id=1, model=model, role_data=role_data)

        print(f"✅ 智能体创建成功")
        print(f"   - ID: {agent.unique_id}")
        print(f"   - 描述类型: {type(agent.description)}")
        print(f"   - 智能体类型: {type(agent).__name__}")

        # 检查游戏状态初始化
        game_state = agent.context["game_state"]
        print(f"   - 存活状态: {game_state['is_alive']}")
        print(f"   - 伪装身份: {game_state['fake_role']}")
        print(f"   - 怀疑度: {game_state['suspicion_level']}")

        # 显示思维链初始化情况
        if hasattr(agent, 'chains'):
            print(f"   - 思维链数量: {len(agent.chains)}")
            print(f"   - 思维链名称: {list(agent.chains.keys())}")
        else:
            print(f"   - 思维链: 未初始化")

        return True, (agent, model)

    except Exception as e:
        print(f"❌ 智能体创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_prompt_templates():
    """测试prompt模板加载"""
    print("\n" + "="*50)
    print("🧪 测试2: Prompt模板加载")
    print("="*50)

    model = MockModel()

    # 测试模板列表
    templates = [
        "werewolf/night_action.txt",
        "werewolf/day_discussion.txt",
        "werewolf/defense.txt",
        "werewolf/voting.txt",
        "werewolf/reflect.txt"
    ]

    all_success = True

    for template_name in templates:
        try:
            template = model.prompt_factory.get_template(template_name)
            print(f"✅ {template_name}: 加载成功")
        except Exception as e:
            print(f"❌ {template_name}: 加载失败 - {e}")
            all_success = False

    return all_success


def test_night_action(agent):
    """测试夜晚行动"""
    print("\n" + "="*50)
    print("🧪 测试3: 夜晚行动")
    print("="*50)

    # 模拟游戏状态
    game_state = {
        "phase": 1,
        "potential_victims": [
            {
                "id": 2,
                "threat_level": "高",
                "role_probability": {"prophet": 0.7, "witch": 0.2, "civilian": 0.1},
                "reason": "发言分析显示可能是神职"
            },
            {
                "id": 3,
                "threat_level": "中",
                "role_probability": {"hunter": 0.4, "civilian": 0.6},
                "reason": "行为相对普通"
            }
        ],
        "teammates": [{"id": 4, "status": "alive"}],
        "previous_kills": []
    }

    try:
        # 执行夜晚行动
        result = agent.night_action(game_state)

        print("✅ 夜晚行动执行成功")
        print(f"   - 结果: {result}")

        # 检查结果格式
        if "target_id" in result:
            print(f"   - 目标: {result['target_id']}")
        if "reason" in result:
            print(f"   - 理由: {result['reason']}")

        return True

    except Exception as e:
        print(f"❌ 夜晚行动执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_day_discussion(agent):
    """测试白天讨论"""
    print("\n" + "="*50)
    print("🧪 测试4: 白天讨论")
    print("="*50)

    # 模拟游戏状态
    game_state = {
        "phase": 2,
        "phase_name": "白天讨论",
        "alive_count": 8,
        "speak_order": 3,
        "last_night_result": "昨晚2号玩家被淘汰",
        "already_spoken": [
            {
                "player_id": 5,
                "content": "我觉得2号很可疑，昨晚的击杀选择很奇怪",
                "suspicion_indicators": [
                    {"description": "过于激进", "severity": "中"}
                ]
            }
        ],
        "urgent_situation": None
    }

    try:
        # 执行白天讨论
        result = agent.day_discussion(game_state)

        print("✅ 白天讨论执行成功")
        print(f"   - 发言内容: {result[:100]}..." if len(result) > 100 else f"   - 发言内容: {result}")

        return True

    except Exception as e:
        print(f"❌ 白天讨论执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_defense(agent):
    """测试辩护"""
    print("\n" + "="*50)
    print("🧪 测试5: 辩护")
    print("="*50)

    # 模拟被质疑的场景
    accusations = [
        {
            "accuser_id": 3,
            "content": "1号的投票行为很可疑，总是投票给好人",
            "evidence": "投票记录显示",
            "severity": "高"
        }
    ]

    extra_data = {
        "suspicion_level": 0.8,
        "accusers": [3, 5],
        "vote_risk": "high"
    }

    try:
        # 执行辩护
        result = agent.defense(accusations, extra_data)

        print("✅ 辩护执行成功")
        print(f"   - 辩护内容: {result[:100]}..." if len(result) > 100 else f"   - 辩护内容: {result}")

        return True

    except Exception as e:
        print(f"❌ 辩护执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_voting(agent):
    """测试投票"""
    print("\n" + "="*50)
    print("🧪 测试6: 投票")
    print("="*50)

    # 模拟投票场景
    candidates = [
        {
            "id": 2,
            "current_votes": 2,
            "suspicion_reason": "发言逻辑有问题",
            "role_guess": "预言家",
            "is_teammate": False
        },
        {
            "id": 6,
            "current_votes": 1,
            "suspicion_reason": "投票异常",
            "role_guess": "平民",
            "is_teammate": True
        }
    ]

    extra_data = {
        "voting_round": 3,
        "voting_reason": "针对2号玩家的投票",
        "alive_count": 7,
        "urgent_vote": False,
        "werewolf_advantage": False
    }

    try:
        # 执行投票
        result = agent.vote(candidates, extra_data)

        print("✅ 投票执行成功")
        print(f"   - 投票结果: {result}")

        return True

    except Exception as e:
        print(f"❌ 投票执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reflect(agent):
    """测试反思"""
    print("\n" + "="*50)
    print("🧪 测试7: 反思")
    print("="*50)

    try:
        # 执行反思 (reflect方法不需要参数)
        result = agent.reflect()

        print("✅ 反思执行成功")
        print(f"   - 反思结果: {result}")

        return True

    except Exception as e:
        print(f"❌ 反思执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试 WerewolfAgent")
    print("="*50)

    # 记录测试结果
    test_results = []

    # 测试1: 智能体创建
    creation_result = test_agent_creation()
    if creation_result[0]:
        test_results.append(("智能体创建", True))
        agent = creation_result[1][0]
        model = creation_result[1][1]
    else:
        test_results.append(("智能体创建", False))
        print("\n❌ 智能体创建失败，跳过后续测试")
        return False

    # 测试2: Prompt模板加载
    template_result = test_prompt_templates()
    test_results.append(("Prompt模板加载", template_result))

    # 测试3-7: 智能体方法
    methods_to_test = [
        ("夜晚行动", test_night_action),
        ("白天讨论", test_day_discussion),
        ("辩护", test_defense),
        ("投票", test_voting),
        ("反思", test_reflect)
    ]

    for method_name, test_func in methods_to_test:
        try:
            result = test_func(agent)
            test_results.append((method_name, result))
        except Exception as e:
            print(f"❌ {method_name}测试异常: {e}")
            test_results.append((method_name, False))

    # 输出测试总结
    print("\n" + "="*50)
    print("📊 测试结果总结")
    print("="*50)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过！WerewolfAgent 实现正确。")
        return True
    else:
        print("⚠️  部分测试失败，需要修复问题。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)