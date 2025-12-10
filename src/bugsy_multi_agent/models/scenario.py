from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """
    Тестовый сценарий, покрывающий один или несколько атрибутов.
    """

    id: str
    title: str
    steps: List[str] = Field(default_factory=list)
    expected_result: str
    attributes_covered: List[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Scenario":
        return cls.model_validate(data)
