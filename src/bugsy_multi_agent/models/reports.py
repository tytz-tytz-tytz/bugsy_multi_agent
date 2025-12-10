from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


Severity = Literal["info", "warning", "error"]


class ValidationIssue(BaseModel):
    """
    Одна проблема валидации: что не так, где и насколько критично.
    """

    severity: Severity
    code: str
    message: str
    object_type: str  # "attribute" или "scenario" и т.п.
    object_id: Optional[str] = None
    field: Optional[str] = None


class ValidationReport(BaseModel):
    """
    Результат работы валидатора.
    """

    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    summary: str = ""

    def add_issue(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)
        if issue.severity == "error":
            self.is_valid = False


class AttributeCoverageEntry(BaseModel):
    """
    Покрытие для одной сущности: какой атрибут/что её покрывает.
    """

    entity_id: str
    entity_type: str  # "domain_entity", "passage"
    description: str
    attribute_ids: List[str] = Field(default_factory=list)


class AttributeCoverageReport(BaseModel):
    """
    Покрытие domain_entities и core_passages атрибутами.
    """

    query: str
    covered: List[AttributeCoverageEntry] = Field(default_factory=list)
    uncovered: List[AttributeCoverageEntry] = Field(default_factory=list)
    summary: str = ""


class ScenarioCoverageEntry(BaseModel):
    """
    Покрытие одного атрибута сценариями.
    """

    attribute_id: str
    scenario_ids: List[str] = Field(default_factory=list)


class ScenarioCoverageReport(BaseModel):
    """
    Покрытие атрибутов сценариями.
    """

    query: str
    attribute_coverage: List[ScenarioCoverageEntry] = Field(default_factory=list)
    attributes_without_scenarios: List[str] = Field(default_factory=list)
    scenarios_without_attributes: List[str] = Field(default_factory=list)
    summary: str = ""
