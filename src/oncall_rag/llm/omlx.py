from __future__ import annotations

import json

import httpx

from oncall_rag.llm.base import LLMClient


class OmlxClient(LLMClient):
    def __init__(self, endpoint: str, model: str, system_prompt: str | None = None):
        super().__init__(system_prompt)
        self.endpoint = endpoint.rstrip("/")
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        payload = {
            "model": self.model,
            "prompt": f"{self.system_prompt}\n\n{prompt}",
            "stream": False,
            "options": {"temperature": 0, "num_predict": 1024},
        }
        response = httpx.post(
            f"{self.endpoint}/api/generate",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
