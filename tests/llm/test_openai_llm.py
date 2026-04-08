"""openai_llm.py 模块单元测试。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from casevo.llm.openai_llm import OpenAI_LLM
from casevo.llm_interface import LLMConfig


def _build_chat_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=None))]
    )


def _build_embedding_response(*vectors):
    return SimpleNamespace(data=[SimpleNamespace(embedding=list(item)) for item in vectors])


def _build_mock_client():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _build_chat_response("ok")
    mock_client.embeddings.create.return_value = _build_embedding_response([0.1, 0.2])
    return mock_client


def test_init_params_are_passed_to_openai_client():
    mock_client = _build_mock_client()

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client) as openai_cls:
        llm = OpenAI_LLM(api_key="test-key", base_url="http://localhost:8000/v1")

    openai_cls.assert_called_once_with(api_key="test-key", base_url="http://localhost:8000/v1")
    assert llm.default_model == "gpt-4o"


def test_send_message_returns_text():
    mock_client = _build_mock_client()
    mock_client.chat.completions.create.return_value = _build_chat_response("hello")

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client):
        llm = OpenAI_LLM(api_key="test-key")

    result = llm.send_message("你好")

    assert result == "hello"
    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o"
    assert kwargs["messages"] == [{"role": "user", "content": "你好"}]


def test_send_message_by_config_maps_llm_config_fields():
    mock_client = _build_mock_client()
    mock_client.chat.completions.create.return_value = _build_chat_response('{"ok":true}')

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client):
        llm = OpenAI_LLM(api_key="test-key")

    cfg = LLMConfig(system="你是助手", model="gpt-4.1", temperature=0.6, max_tokens=128)
    result = llm.send_message_by_config("测试", cfg, json_flag=True)

    assert result == '{"ok":true}'
    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4.1"
    assert kwargs["temperature"] == 0.6
    assert kwargs["max_tokens"] == 128
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["messages"][0] == {"role": "system", "content": "你是助手"}


def test_send_embedding_returns_list_of_vectors():
    mock_client = _build_mock_client()
    mock_client.embeddings.create.return_value = _build_embedding_response([0.1, 0.2], [0.3, 0.4])

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client):
        llm = OpenAI_LLM(api_key="test-key")

    result = llm.send_embedding(["a", "b"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    kwargs = mock_client.embeddings.create.call_args.kwargs
    assert kwargs["model"] == "text-embedding-3-small"
    assert kwargs["input"] == ["a", "b"]


def test_get_lang_embedding_returns_callable_embedding_function():
    mock_client = _build_mock_client()
    mock_client.embeddings.create.return_value = _build_embedding_response([0.11, 0.22])

    with patch("casevo.llm.openai_llm.OpenAI", return_value=mock_client):
        llm = OpenAI_LLM(api_key="test-key")

    embedding_fn = llm.get_lang_embedding()
    result = embedding_fn(["x"])

    assert result == [[0.11, 0.22]]
    kwargs = mock_client.embeddings.create.call_args.kwargs
    assert kwargs["model"] == "text-embedding-3-small"
    assert kwargs["input"] == ["x"]
