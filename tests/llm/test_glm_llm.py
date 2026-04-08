"""glm_llm.py 模块单元测试。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from casevo.llm.glm_llm import GLM_LLM
from casevo.llm_interface import LLMConfig


def _build_chat_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=None))]
    )


def _build_embedding_response(*vectors):
    return SimpleNamespace(data=[SimpleNamespace(embedding=list(item)) for item in vectors])


def _build_mock_client():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _build_chat_response("glm-ok")
    mock_client.embeddings.create.return_value = _build_embedding_response([1.0, 2.0])
    return mock_client


def test_init_default_params_for_glm():
    mock_client = _build_mock_client()

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client) as openai_cls:
        llm = GLM_LLM(api_key="glm-key")

    openai_cls.assert_called_once_with(
        api_key="glm-key",
        base_url="https://open.bigmodel.cn/api/paas/v4",
    )
    assert llm.default_model == "glm-4"


def test_send_message_returns_text_with_glm_default_model():
    mock_client = _build_mock_client()
    mock_client.chat.completions.create.return_value = _build_chat_response("glm-hello")

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client):
        llm = GLM_LLM(api_key="glm-key")

    result = llm.send_message("你好")

    assert result == "glm-hello"
    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "glm-4"
    assert kwargs["messages"] == [{"role": "user", "content": "你好"}]


def test_send_message_by_config_uses_config_model_and_system():
    mock_client = _build_mock_client()
    mock_client.chat.completions.create.return_value = _build_chat_response("ok")

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client):
        llm = GLM_LLM(api_key="glm-key")

    config = LLMConfig(system="系统提示", model="glm-4-plus", temperature=0.2, max_tokens=64)
    result = llm.send_message_by_config("测试", config)

    assert result == "ok"
    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "glm-4-plus"
    assert kwargs["temperature"] == 0.2
    assert kwargs["max_tokens"] == 64
    assert kwargs["messages"][0] == {"role": "system", "content": "系统提示"}


def test_send_embedding_uses_glm_embedding_model():
    mock_client = _build_mock_client()
    mock_client.embeddings.create.return_value = _build_embedding_response([9.9, 8.8], [7.7, 6.6])

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client):
        llm = GLM_LLM(api_key="glm-key")

    result = llm.send_embedding(["a", "b"])

    assert result == [[9.9, 8.8], [7.7, 6.6]]
    kwargs = mock_client.embeddings.create.call_args.kwargs
    assert kwargs["model"] == "embedding-3"
    assert kwargs["input"] == ["a", "b"]


def test_get_lang_embedding_returns_callable_embedding_function():
    mock_client = _build_mock_client()
    mock_client.embeddings.create.return_value = _build_embedding_response([3.3, 4.4])

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client):
        llm = GLM_LLM(api_key="glm-key")

    embedding_fn = llm.get_lang_embedding()
    result = embedding_fn(["content"])

    assert result == [[3.3, 4.4]]
    kwargs = mock_client.embeddings.create.call_args.kwargs
    assert kwargs["model"] == "embedding-3"
    assert kwargs["input"] == ["content"]
