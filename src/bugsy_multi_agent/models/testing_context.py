from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Passage(BaseModel):
    section_id: str
    title: str
    role: Literal["core", "supporting", "edge_case"] = "core"
    importance: Literal["high", "medium", "low"] = "medium"
    summary: str = ""


class TestingContext(BaseModel):
    """
    Стандартизированный контекст, который выдаёт OntologyRAG Retriever Agent,
    и который потребляют все остальные агенты пайплайна.
    """

    query: str
    focus_summary: str
    core_passages: List[Passage] = Field(default_factory=list)
    supporting_passages: List[Passage] = Field(default_factory=list)
    discarded_sections: List[str] = Field(default_factory=list)
    domain_entities: List[str] = Field(default_factory=list)
    hints_for_tests: List[str] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "TestingContext":
        """
        Удобный конструктор из произвольного dict.
        """
        return cls.model_validate(data)

    def to_dict(self) -> dict:
        """
        Преобразует объект в обычный dict, готовый к json.dump.
        """
        return self.model_dump()
