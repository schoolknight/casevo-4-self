# 狼人杀AI智能体实现

基于Casevo框架和Jinja2模板系统实现的狼人杀AI智能体，专注于狼人角色的完整行为逻辑。

## 项目结构

```
app/
├── agents/                      # 智能体实现
│   ├── __init__.py             # 模块初始化
│   └── werewolf.py             # 狼人智能体主类
├── prompts/                    # Jinja2模板系统
│   ├── werewolf/               # 狼人专用模板
│   │   ├── night_action.j2     # 夜晚击杀行动模板
│   │   ├── day_discussion.j2   # 白天讨论发言模板
│   │   ├── defense.j2          # 被质疑时辩护模板
│   │   └── voting.j2           # 投票决策模板
│   └── common/                 # 通用模板
│       └── role_reveal.j2      # 身份公布模板
├── utils/                      # 工具模块
│   ├── template_manager.py     # 模板管理器
│   └── werewolf_example.py     # 使用示例
└── llm/                        # 语言模型接口
    ├── chatgpt.py              # ChatGPT接口
    ├── chatglm.py              # ChatGLM接口
    └── config.py               # 配置管理
```

## 核心特性

### 1. 完整的狼人行为逻辑
- **夜晚击杀**: 基于威胁评估的智能击杀决策
- **白天发言**: 伪装身份的讨论发言生成
- **辩护系统**: 面对质疑时的策略性辩护
- **投票决策**: 综合考虑风险的投票策略

### 2. Jinja2模板系统
- **动态内容**: 支持复杂的变量替换和条件渲染
- **结构化管理**: 分角色、分场景的模板组织
- **缓存优化**: 模板加载和渲染性能优化

### 3. 角色人设集成
- **个性化AI**: 基于person.json中的角色人设数据
- **决策权重**: 量化的决策权重支持概率计算
- **策略框架**: 分阶段的详细游戏策略指导

### 4. Casevo框架兼容
- **基类继承**: 完全兼容AgentBase基类
- **思维链系统**: 支持多步骤的复杂推理过程
- **记忆系统**: 集成短期和长期记忆管理

## 快速开始

### 1. 环境准备
确保已安装必要的依赖：
```bash
pip install jinja2
pip install casevo  # Casevo框架
```

### 2. 角色人设数据
确保`.claude/doc/profile/person.json`文件存在，包含狼人角色的人设数据。

### 3. 基础使用示例

```python
from app.agents.werewolf import create_werewolf_agent
import json

# 加载角色数据
with open('.claude/doc/profile/person.json', 'r', encoding='utf-8') as f:
    roles = json.load(f)

werewolf_data = next(role for role in roles if role['id'] == 'werewolf')

# 创建狼人智能体
werewolf = create_werewolf_agent(
    unique_id=1,
    model=your_game_model,
    role_data=werewolf_data
)

# 设置伪装身份
werewolf.set_fake_role("civilian")

# 夜晚行动
game_state = your_game_state
kill_result = werewolf.night_action(game_state)

# 白天发言
statement = werewolf.day_discussion(game_state)
```

## 模板系统详解

### 模板变量体系

#### agent.* - 智能体属性
```jinja2
{{agent.role}}              # 角色名称
{{agent.teammates}}         # 狼队友信息
{{agent.suspicion_level}}  # 被怀疑程度
{{agent.fake_role}}         # 伪装身份
```

#### game.* - 游戏状态
```jinja2
{{game.phase}}              # 游戏轮次
{{game.alive_players}}      # 存活玩家列表
{{game.last_night_result}}  # 昨晚结果
{{game.potential_victims}}  # 潜在受害者
```

#### extra.* - 动态参数
```jinja2
{{extra.already_spoken}}    # 已发言内容
{{extra.teammate_suggestions}} # 队友建议
{{extra.urgent_situation}}  # 紧急情况
```

### 模板高级功能

#### 条件渲染
```jinja2
{% if player.is_teammate %}
[注意：这是你的狼队友]
{% endif %}

{% if game.urgent_situation %}
**紧急状况**：{{game.urgent_situation}}
{% endif %}
```

#### 循环处理
```jinja2
{% for player in game.potential_victims %}
**{{player.id}}号玩家**：
- 威胁等级：{{player.threat_level}}
- 可疑行为：{{player.suspicious_behaviors}}
{% endfor %}
```

## 核心类和方法

### WerewolfAgent类

#### 主要方法
- `night_action(game_state)`: 夜晚击杀决策
- `day_discussion(game_state, context)`: 白天讨论发言
- `defense(accusations, game_state)`: 辩护发言
- `vote(candidates, game_state)`: 投票决策
- `reflect()`: 反思和学习

#### 状态管理
- `get_agent_state()`: 获取当前状态
- `update_suspicion(level)`: 更新被怀疑程度
- `set_fake_role(role, description)`: 设置伪装身份
- `add_teammate(id, info)`: 添加狼队友

### TemplateManager类

#### 主要功能
- `render_template(path, **kwargs)`: 渲染指定模板
- `render_werewolf_template(name, agent, game, extra)`: 渲染狼人模板
- `validate_template_variables(path, variables)`: 验证模板变量
- `batch_render(configs)`: 批量渲染模板

## 使用示例

### 1. 夜晚击杀行动
```python
# 准备游戏状态
game_state = {
    "phase": 1,
    "phase_name": "第一夜",
    "potential_victims": [
        {"id": 2, "threat_level": "high"},
        {"id": 5, "threat_level": "medium"}
    ]
}

# 执行夜晚行动
result = werewolf.night_action(game_state)
print(f"击杀目标: {result['target']}")
print(f"行动理由: {result['reason']}")
```

### 2. 白天讨论发言
```python
# 准备白天游戏状态
game_state = {
    "phase": 1,
    "phase_name": "第一天白天",
    "last_night_result": "昨晚2号玩家被击杀",
    "already_spoken": [
        {"player_id": 3, "content": "我们需要找出狼人"}
    ]
}

# 生成发言内容
statement = werewolf.day_discussion(game_state)
print(f"发言内容: {statement}")
```

### 3. 投票决策
```python
# 准备候选人
candidates = [
    {"id": 3, "suspicion_level": 0.3},
    {"id": 4, "suspicion_level": 0.6}
]

# 投票决策
vote_result = werewolf.vote(candidates, game_state)
print(f"投票目标: {vote_result['vote_target']}")
print(f"投票理由: {vote_result['reason']}")
```

## 运行示例

项目包含完整的使用示例，可以直接运行：

```bash
cd /Users/jiangzx/Project/github/casevo-4-self
python app/utils/werewolf_example.py
```

示例包括：
- 模板系统使用演示
- 夜晚行动示例
- 白天讨论示例
- 投票决策示例

## 扩展开发

### 添加新角色模板
1. 在`app/prompts/`下创建新的角色目录
2. 设计对应角色的Jinja2模板
3. 在`WerewolfAgent`中添加新的思维链
4. 实现角色特有的方法

### 自定义模板变量
1. 修改`_prepare_agent_data()`方法
2. 扩展`_prepare_*_extra_data()`方法
3. 更新模板中的变量使用

### 集成到游戏系统
1. 实现`get_game_state()`方法
2. 设置适当的游戏上下文
3. 集成思维链执行机制

## 注意事项

1. **依赖要求**: 确保Jinja2和相关依赖已正确安装
2. **配置文件**: LLM配置需要正确设置
3. **角色数据**: person.json文件需要包含完整的角色人设
4. **模板路径**: 模板文件路径需要正确配置

## 性能优化

1. **模板缓存**: 自动缓存已加载的模板
2. **批量渲染**: 支持批量模板渲染
3. **变量验证**: 预验证模板变量完整性
4. **错误处理**: 完善的错误处理和降级策略

这个实现为狼人杀AI智能体提供了完整、可扩展的基础框架，支持复杂的角色扮演和策略决策。