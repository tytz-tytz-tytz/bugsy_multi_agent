from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

from openai import OpenAI


class LLMClient(ABC):
    """
    Абстрактный клиент LLM.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Синхронный вызов LLM: принимает текстовый промпт, возвращает текстовый ответ.
        """
        raise NotImplementedError


class DummyLLMClient(LLMClient):
    """
    Временная заглушка, если LLM не настроен.
    """

    def generate(self, prompt: str) -> str:
        raise NotImplementedError(
            "DummyLLMClient: LLM is not configured. "
            "Use DeepSeekLLMClient instead."
        )


class DeepSeekLLMClient(LLMClient):
    """
    Клиент для DeepSeek API через OpenAI SDK.

    Использует:
    - base_url = https://api.deepseek.com
    - API-ключ из переменной окружения DEEPSEEK_API_KEY
    - модель по умолчанию: deepseek-chat
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        temperature: float = 0.2,
    ) -> None:
        if api_key is None:
            api_key = os.environ.get("DEEPSEEK_API_KEY")

        if not api_key:
            raise RuntimeError(
                "DeepSeekLLMClient: API key is not set. "
                "Set DEEPSEEK_API_KEY environment variable."
            )

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature

    def generate(self, prompt: str) -> str:
        """
        Делает запрос к DeepSeek chat.completions.

        Мы используем:
        - system: роль сервиса, который обязан вернуть строго JSON.
        - user: наш промпт с описанием формата.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a backend JSON generator. "
                        "You must respond with STRICT JSON only, "
                        "matching the user's schema description. "
                        "No explanations, no comments, no markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            stream=False,
        )
        return response.choices[0].message.content
