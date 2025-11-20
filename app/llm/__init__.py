"""
LLM模块初始化文件
"""
from .chatgpt import ChatGPTLLM
from .chatglm import ChatGLMLLM
from .config import LLM_CONFIG, get_config, validate_config

__all__ = [
    'ChatGPTLLM',
    'ChatGLMLLM',
    'LLM_CONFIG',
    'get_config',
    'validate_config'
]


def create_llm(provider: str, **kwargs):
    """
    创建LLM实例的工厂函数

    Args:
        provider: LLM提供商名称 ('chatgpt' 或 'chatglm')
        **kwargs: 额外的配置参数，会覆盖默认配置

    Returns:
        LLM实例

    Raises:
        ValueError: 当提供商不支持或配置无效时
    """
    config = get_config(provider)

    # 合并用户提供的参数
    config.update(kwargs)

    if provider == 'chatgpt':
        return ChatGPTLLM(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model=config['model'],
            embedding_model=config['embedding_model'],
            temperature=config['temperature'],
            max_tokens=config['max_tokens']
        )
    elif provider == 'chatglm':
        return ChatGLMLLM(
            api_key=config['api_key'],
            model=config['model'],
            embedding_model=config['embedding_model'],
            temperature=config['temperature'],
            max_tokens=config['max_tokens']
        )
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")


def list_available_providers():
    """
    列出所有可用的LLM提供商

    Returns:
        提供商列表
    """
    providers = []
    for provider in LLM_CONFIG.keys():
        if validate_config(provider):
            providers.append(provider)
    return providers