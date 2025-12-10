from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field


AttributeType = Literal["business_rule", "functional", "ui", "negative"]
Priority = Literal["P1", "P2", "P3"]


class Attribute(BaseModel):
    """
    Атомарное тестируемое требование/правило.
    """

    id: str
    name: str
    type: AttributeType
    priority: Priority
    description: str

    positive_example: str
    negative_example: str

    source_section_ids: List[str] = Field(default_factory=list)
    source_quotes: List[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Attribute":
        return cls.model_validate(data)
