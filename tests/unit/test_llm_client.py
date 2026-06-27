from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from oncall_rag.llm.anthropic import AnthropicClient
from oncall_rag.llm.base import LLMClient
from oncall_rag.llm.omlx import OmlxClient
from oncall_rag.llm.openai import OpenAIClient


class TestLLMClientBase:
    def test_abc_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            LLMClient()

    def test_default_system_prompt(self):
        class FakeClient(LLMClient):
            def generate(self, prompt, **kwargs):
                return ""

        client = FakeClient()
        assert "on-call assistant" in client.system_prompt
        assert "don't have a runbook" in client.system_prompt

    def test_custom_system_prompt(self):
        class FakeClient(LLMClient):
            def generate(self, prompt, **kwargs):
                return ""

        client = FakeClient(system_prompt="Custom prompt")
        assert client.system_prompt == "Custom prompt"


class TestOmlxClient:
    def test_generate_success(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:11434/api/generate",
            json={"response": "Check kubectl describe pod."},
        )
        client = OmlxClient(endpoint="http://localhost:11434", model="qwen2.5-coder:7b")
        result = client.generate("How to debug a pod?")
        assert result == "Check kubectl describe pod."

    def test_generate_handles_empty_response(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:11434/api/generate",
            json={"response": ""},
        )
        client = OmlxClient(endpoint="http://localhost:11434", model="qwen2.5-coder:7b")
        result = client.generate("test")
        assert result == ""

    def test_generate_raises_on_http_error(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:11434/api/generate",
            status_code=503,
        )
        client = OmlxClient(endpoint="http://localhost:11434", model="qwen2.5-coder:7b")
        with pytest.raises(httpx.HTTPStatusError):
            client.generate("test")

    def test_strips_trailing_slash_from_endpoint(self):
        client = OmlxClient(endpoint="http://localhost:11434/", model="m")
        assert client.endpoint == "http://localhost:11434"

    def test_includes_system_prompt(self, httpx_mock):
        httpx_mock.add_response(
            url="http://localhost:11434/api/generate",
            json={"response": "answer"},
        )
        client = OmlxClient(
            endpoint="http://localhost:11434",
            model="m",
            system_prompt="You are helpful.",
        )
        client.generate("test")
        request = httpx_mock.get_requests()[0]
        assert b"You are helpful." in request.content


class TestOpenAIClient:
    def test_generate_success(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Check the logs."
        with patch("oncall_rag.llm.openai.OpenAI") as mock_openai:
            instance = mock_openai.return_value
            instance.chat.completions.create.return_value = mock_response
            client = OpenAIClient(api_key="sk-test", model="gpt-4o-mini")
            result = client.generate("How to debug?")
        assert result == "Check the logs."

    def test_generate_returns_empty_on_no_content(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        with patch("oncall_rag.llm.openai.OpenAI") as mock_openai:
            instance = mock_openai.return_value
            instance.chat.completions.create.return_value = mock_response
            client = OpenAIClient(api_key="sk-test", model="gpt-4o-mini")
            result = client.generate("test")
        assert result == ""

    def test_passes_correct_parameters(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "answer"
        with patch("oncall_rag.llm.openai.OpenAI") as mock_openai:
            instance = mock_openai.return_value
            instance.chat.completions.create.return_value = mock_response
            client = OpenAIClient(api_key="sk-test", model="gpt-4o-mini")
            client.generate("What is on-call?")
            instance.chat.completions.create.assert_called_once_with(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": client.system_prompt},
                    {"role": "user", "content": "What is on-call?"},
                ],
                temperature=0,
                max_tokens=1024,
            )


class TestAnthropicClient:
    def test_generate_success(self):
        mock_block = MagicMock()
        mock_block.text = "Restart the service."
        mock_response = MagicMock()
        mock_response.content = [mock_block]

        with patch("oncall_rag.llm.anthropic.Anthropic") as mock_anthropic:
            instance = mock_anthropic.return_value
            instance.messages.create.return_value = mock_response
            client = AnthropicClient(api_key="sk-ant-test", model="claude-3-haiku-20240307")
            result = client.generate("How to fix?")
        assert result == "Restart the service."

    def test_generate_returns_empty_on_no_content(self):
        mock_response = MagicMock()
        mock_response.content = []

        with patch("oncall_rag.llm.anthropic.Anthropic") as mock_anthropic:
            instance = mock_anthropic.return_value
            instance.messages.create.return_value = mock_response
            client = AnthropicClient(api_key="sk-ant-test", model="claude-3-haiku-20240307")
            result = client.generate("test")
        assert result == ""

    def test_passes_correct_parameters(self):
        mock_block = MagicMock()
        mock_block.text = "answer"
        mock_response = MagicMock()
        mock_response.content = [mock_block]

        with patch("oncall_rag.llm.anthropic.Anthropic") as mock_anthropic:
            instance = mock_anthropic.return_value
            instance.messages.create.return_value = mock_response
            client = AnthropicClient(api_key="sk-ant-test", model="claude-3-haiku-20240307")
            client.generate("What is an incident?")
            instance.messages.create.assert_called_once_with(
                model="claude-3-haiku-20240307",
                system=client.system_prompt,
                messages=[{"role": "user", "content": "What is an incident?"}],
                temperature=0,
                max_tokens=1024,
            )
