import asyncio
from typing import Any, Optional

import aiohttp


class LLMError(Exception):
    pass


class OllamaClient:

    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_api_url(self, endpoint: str) -> str:
        return f"{self.base_url}/api/{endpoint}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,
    ) -> dict:
        url = self._get_api_url(endpoint)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.request(method, url, json=json_data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise LLMError(f"Ollama API error {resp.status}: {text}")
                return await resp.json()

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system
        if max_tokens:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = max_tokens

        result = await self._request("POST", "generate", json_data=payload)
        return result.get("response", "").strip()

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        result = await self._request("POST", "chat", json_data=payload)
        message = result.get("message", {})
        return message.get("content", "").strip()

    def ask(self, prompt: str, system: Optional[str] = None, **kwargs: Any) -> str:
        return asyncio.run(self.generate(prompt, system=system, **kwargs))

    def chat_sync(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        return asyncio.run(self.chat(messages, **kwargs))

    async def check_available(self) -> bool:
        try:
            result = await self._request("GET", "tags")
            models = result.get("models", [])
            model_names = [m.get("name", "") for m in models]
            return any(self.model in name for name in model_names)
        except (LLMError, aiohttp.ClientError, asyncio.TimeoutError):
            return False
