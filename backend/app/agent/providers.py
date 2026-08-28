"""AI provider abstraction for Network Copilot."""
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional
import os
import json
import httpx


class AIProvider(ABC):
    """Base AI provider interface."""

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        """Send chat messages and return response."""
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        """Stream chat response tokens."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")

    def name(self) -> str:
        return "openai"

    async def chat(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": messages, **kwargs},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": messages, "stream": True, **kwargs},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[6:])
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = "https://api.anthropic.com"

    def name(self) -> str:
        return "anthropic"

    async def chat(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        system = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": kwargs.get("max_tokens", 4096),
                    "system": system,
                    "messages": chat_messages,
                },
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]

    async def chat_stream(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        system = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": kwargs.get("max_tokens", 4096),
                    "system": system,
                    "messages": chat_messages,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "content_block_delta":
                                yield data.get("delta", {}).get("text", "")
                        except (json.JSONDecodeError, KeyError):
                            pass


class OllamaProvider(AIProvider):
    """Ollama local LLM provider."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    def name(self) -> str:
        return "ollama"

    async def chat(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        model = model or os.getenv("OLLAMA_MODEL", "llama3")
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    async def chat_stream(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        model = model or os.getenv("OLLAMA_MODEL", "llama3")
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            yield data.get("message", {}).get("content", "")
                        except json.JSONDecodeError:
                            pass


class NineRouterProvider(AIProvider):
    """9Router model gateway provider."""

    FREE_COMBOS = {
        "opencode-go": "Fast free model for quick tasks",
        "opencode-zen": "Balanced free model for general work",
        "opencode-cheap": "Scout mode, cheapest available",
    }

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("NINEROUTER_URL", "http://127.0.0.1:20128")).rstrip("/")
        self.api_key = api_key or os.getenv("NINEROUTER_KEY", "")

    def name(self) -> str:
        return "9router"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        model = model or os.getenv("NINEROUTER_MODEL", "opencode-coder")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": messages, **kwargs},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict[str, str]], model: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        model = model or os.getenv("NINEROUTER_MODEL", "opencode-coder")
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": messages, "stream": True, **kwargs},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[6:])
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass

    async def web_search(self, query: str, max_results: int = 5, search_type: str = "web", **kwargs) -> dict[str, Any]:
        """Search the web via 9Router /v1/search."""
        model = os.getenv("NINEROUTER_SEARCH_MODEL", "search-combo")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/v1/search",
                headers=self._headers(),
                json={
                    "model": model,
                    "query": query,
                    "max_results": max_results,
                    "search_type": search_type,
                    **kwargs,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def web_fetch(self, url: str, format: str = "markdown", max_characters: int = 12000) -> dict[str, Any]:
        """Fetch webpage content via 9Router /v1/web/fetch."""
        model = os.getenv("NINEROUTER_FETCH_MODEL", "fetch-combo")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/v1/web/fetch",
                headers=self._headers(),
                json={
                    "model": model,
                    "url": url,
                    "format": format,
                    "max_characters": max_characters,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def list_models(self) -> dict[str, Any]:
        """List available models from 9Router."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/v1/models",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return {"data": []}

    def get_free_models(self) -> list[dict[str, str]]:
        """Return available free model combos."""
        return [
            {"id": name, "name": name, "description": desc, "tier": "free"}
            for name, desc in self.FREE_COMBOS.items()
        ]


def get_provider(name: Optional[str] = None) -> AIProvider:
    """Get AI provider by name. Defaults to settings or OpenAI."""
    provider_name = name or os.getenv("AI_PROVIDER", "openai")

    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "9router": NineRouterProvider,
    }

    provider_class = providers.get(provider_name, OpenAIProvider)
    return provider_class()
