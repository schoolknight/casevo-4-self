"""
LLM模块使用示例
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from casevo.llm_interface import LLM_INTERFACE
except ImportError:
    # 如果无法导入，继续运行示例（LLM_INTERFACE在这个文件中不是必需的）
    pass

from app.llm import ChatGPTLLM, ChatGLMLLM, create_llm, validate_config, list_available_providers


def example_chatgpt():
    """ChatGPT使用示例"""
    print("=== ChatGPT 使用示例 ===")

    # 检查配置
    if not validate_config('chatgpt'):
        print("请设置 OPENAI_API_KEY 环境变量")
        return

    # 创建ChatGPT实例
    try:
        from app.llm.config import get_config
        config = get_config('chatgpt')

        chatgpt = ChatGPTLLM(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model=config['model'],
            embedding_model=config['embedding_model'],
            temperature=config['temperature'],
            max_tokens=config['max_tokens']
        )

        # 发送消息
        prompt = "你好，请简单介绍一下狼人杀游戏的基本规则"
        print(f"发送: {prompt}")

        response = chatgpt.send_message(prompt)
        print(f"回复: {response}")

        # 测试嵌入功能
        texts = ["狼人杀是一个推理游戏", "预言家可以查验身份", "狼人需要隐藏身份"]
        print(f"\n测试嵌入功能，文本数量: {len(texts)}")

        embeddings = chatgpt.send_embedding(texts)
        if embeddings:
            print(f"成功获取 {len(embeddings)} 个嵌入向量")
            print(f"第一个向量维度: {len(embeddings[0])}")
        else:
            print("嵌入功能测试失败")

    except Exception as e:
        print(f"ChatGPT示例执行失败: {str(e)}")


def example_chatglm():
    """ChatGLM使用示例"""
    print("\n=== ChatGLM 使用示例 ===")

    # 检查配置
    if not validate_config('chatglm'):
        print("请设置 CHATGLM_API_KEY 环境变量")
        return

    # 创建ChatGLM实例
    try:
        from app.llm.config import get_config
        config = get_config('chatglm')

        chatglm = ChatGLMLLM(
            api_key=config['api_key'],
            model=config['model'],
            embedding_model=config['embedding_model'],
            temperature=config['temperature'],
            max_tokens=config['max_tokens']
        )

        # 发送消息
        prompt = "你好，请分析一下狼人杀中预言家角色的重要性"
        print(f"发送: {prompt}")

        response = chatglm.send_message(prompt)
        print(f"回复: {response}")

        # 测试嵌入功能
        texts = ["预言家是好人阵营的核心角色", "每晚可以查验一名玩家身份", "需要保护好预言家角色"]
        print(f"\n测试嵌入功能，文本数量: {len(texts)}")

        embeddings = chatglm.send_embedding(texts)
        if embeddings:
            print(f"成功获取 {len(embeddings)} 个嵌入向量")
            print(f"第一个向量维度: {len(embeddings[0])}")
        else:
            print("嵌入功能测试失败")

    except Exception as e:
        print(f"ChatGLM示例执行失败: {str(e)}")


def example_factory():
    """工厂函数使用示例"""
    print("\n=== 工厂函数使用示例 ===")

    # 列出可用的提供商
    available = list_available_providers()
    print(f"可用的LLM提供商: {available}")

    for provider in available:
        print(f"\n测试 {provider} 提供商:")
        try:
            # 使用工厂函数创建实例
            llm = create_llm(provider)

            # 测试基本功能
            response = llm.send_message("请用一句话介绍你的能力")
            print(f"回复: {response}")

        except Exception as e:
            print(f"测试失败: {str(e)}")


def example_json_response():
    """JSON格式响应示例"""
    print("\n=== JSON格式响应示例 ===")

    if not validate_config('chatgpt'):
        print("请设置 OPENAI_API_KEY 环境变量")
        return

    try:
        from app.llm.config import get_config
        config = get_config('chatgpt')

        chatgpt = ChatGPTLLM(
            api_key=config['api_key'],
            base_url=config['base_url']
        )

        # 请求JSON格式响应
        prompt = """
        请以JSON格式返回狼人杀游戏的基本信息，包含以下字段：
        - name: 游戏名称
        - players: 推荐玩家数量
        - roles: 主要角色列表
        - goal: 游戏目标
        """

        print(f"发送: {prompt}")
        response = chatgpt.send_message(prompt, json_flag=True)
        print(f"JSON回复: {response}")

    except Exception as e:
        print(f"JSON示例执行失败: {str(e)}")


def example_embedding_function():
    """嵌入函数使用示例（与ChromaDB集成）"""
    print("\n=== 嵌入函数使用示例 ===")

    if not validate_config('chatgpt'):
        print("请设置 OPENAI_API_KEY 环境变量")
        return

    try:
        from app.llm.config import get_config
        config = get_config('chatgpt')

        chatgpt = ChatGPTLLM(
            api_key=config['api_key'],
            base_url=config['base_url']
        )

        # 获取ChromaDB兼容的嵌入函数
        embedding_function = chatgpt.get_lang_embedding()

        # 测试文档
        documents = [
            "狼人杀是一款社交推理游戏",
            "玩家分为狼人阵营和好人阵营",
            "通过发言和投票来找出狼人"
        ]

        print(f"处理文档数量: {len(documents)}")

        # 调用嵌入函数
        embeddings = embedding_function(documents)

        print(f"生成嵌入向量数量: {len(embeddings)}")
        print(f"每个向量维度: {len(embeddings[0]) if embeddings else 0}")

    except Exception as e:
        print(f"嵌入函数示例执行失败: {str(e)}")


if __name__ == "__main__":
    print("LLM模块使用示例")
    print("=" * 50)

    # 运行各种示例
    example_chatgpt()
    example_chatglm()
    example_factory()
    example_json_response()
    example_embedding_function()

    print("\n" + "=" * 50)
    print("示例执行完成")