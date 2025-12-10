from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from bugsy_multi_agent.config.settings import Settings


class AgentBase(ABC):
    """
    Базовый класс для всех агентов.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    @abstractmethod
    def run(self, query_id: str) -> Any:
        """
        Запускает агента для указанного query_id.
        Должен прочитать нужные входные JSON и записать результат в свою папку.
        """
        raise NotImplementedError
