from __future__ import annotations

import os
from typing import Any


class LLMClient:
    """Unified LLM client supporting Claude and OpenAI APIs."""

    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider or os.getenv("LLM_PROVIDER", "claude")
        if self.provider == "claude":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
            self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

        self._client: Any = None

    def _get_claude_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def _get_openai_client(self):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ) -> str:
        if self.provider == "claude":
            return await self._generate_claude(system_prompt, user_prompt, max_tokens, temperature)
        else:
            return await self._generate_openai(system_prompt, user_prompt, max_tokens, temperature)

    async def _generate_claude(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        message = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    async def _generate_openai(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        import openai
        client = openai.AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""
