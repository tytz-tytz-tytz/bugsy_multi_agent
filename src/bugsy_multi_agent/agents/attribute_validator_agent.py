from __future__ import annotations

from collections import Counter
from typing import List, Set

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.attribute_store import load_attributes
from bugsy_multi_agent.data_access.attribute_validation_store import (
    save_validation_report,
)
from bugsy_multi_agent.data_access.json_io import read_json
from bugsy_multi_agent.models.attribute import Attribute
from bugsy_multi_agent.models.reports import ValidationIssue, ValidationReport
from bugsy_multi_agent.models.testing_context import TestingContext
from bugsy_multi_agent.orchestration.agent_base import AgentBase


class AttributeValidatorAgent(AgentBase):
    """
    Проверяет сгенерированные атрибуты:
    - уникальность id
    - валидность ссылок на section_id
    - наличие позитивного/негативного примера
    - отсутствие пустых описаний
    """

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings=settings)

    # ---------- загрузка данных ----------

    def _load_testing_context(self, query_id: str) -> TestingContext:
        path = self.settings.ontology_retriever_dir / f"{query_id}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"TestingContext file not found: {path}. "
                f"Run OntologyRAGRetrieverAgent first."
            )
        raw = read_json(path)
        return TestingContext.from_dict(raw)

    def _load_attributes(self, query_id: str) -> List[Attribute]:
        return load_attributes(self.settings, query_id)

    # ---------- проверки ----------

    def _check_unique_ids(
        self, attributes: List[Attribute], report: ValidationReport
    ) -> None:
        ids = [a.id for a in attributes]
        counter = Counter(ids)
        for attr_id, count in counter.items():
            if count > 1:
                report.add_issue(
                    ValidationIssue(
                        severity="error",
                        code="DUPLICATE_ID",
                        message=f"Attribute id '{attr_id}' is not unique ({count} times).",
                        object_type="attribute",
                        object_id=attr_id,
                        field="id",
                    )
                )

    def _check_section_refs(
        self,
        attributes: List[Attribute],
        valid_section_ids: Set[str],
        report: ValidationReport,
    ) -> None:
        for attr in attributes:
            for section_id in attr.source_section_ids:
                if section_id not in valid_section_ids:
                    report.add_issue(
                        ValidationIssue(
                            severity="warning",
                            code="INVALID_SECTION_REF",
                            message=(
                                f"Attribute '{attr.id}' references "
                                f"unknown section_id '{section_id}'."
                            ),
                            object_type="attribute",
                            object_id=attr.id,
                            field="source_section_ids",
                        )
                    )

    def _check_required_fields(
        self,
        attributes: List[Attribute],
        report: ValidationReport,
    ) -> None:
        for attr in attributes:
            if not attr.description.strip():
                report.add_issue(
                    ValidationIssue(
                        severity="error",
                        code="EMPTY_DESCRIPTION",
                        message="Attribute description must not be empty.",
                        object_type="attribute",
                        object_id=attr.id,
                        field="description",
                    )
                )

            if not attr.positive_example.strip():
                report.add_issue(
                    ValidationIssue(
                        severity="error",
                        code="EMPTY_POSITIVE_EXAMPLE",
                        message="Attribute must have a positive_example.",
                        object_type="attribute",
                        object_id=attr.id,
                        field="positive_example",
                    )
                )

            if not attr.negative_example.strip():
                report.add_issue(
                    ValidationIssue(
                        severity="error",
                        code="EMPTY_NEGATIVE_EXAMPLE",
                        message="Attribute must have a negative_example.",
                        object_type="attribute",
                        object_id=attr.id,
                        field="negative_example",
                    )
                )

    # ---------- главный метод ----------

    def run(self, query_id: str) -> ValidationReport:
        """
        Загружает TestingContext и attributes, выполняет проверки
        и сохраняет ValidationReport.
        """
        ctx = self._load_testing_context(query_id)
        attributes = self._load_attributes(query_id)

        report = ValidationReport(is_valid=True, issues=[], summary="")

        # Список валидных section_id из TestingContext
        valid_section_ids: Set[str] = {
            p.section_id for p in ctx.core_passages
        } | {p.section_id for p in ctx.supporting_passages}

        self._check_unique_ids(attributes, report)
        self._check_section_refs(attributes, valid_section_ids, report)
        self._check_required_fields(attributes, report)

        # Итоговое summary
        if not report.issues:
            report.summary = (
                f"{len(attributes)} attributes validated. No issues found."
            )
        else:
            error_count = sum(1 for i in report.issues if i.severity == "error")
            warning_count = sum(1 for i in report.issues if i.severity == "warning")
            report.summary = (
                f"{len(attributes)} attributes validated. "
                f"Errors: {error_count}, warnings: {warning_count}."
            )

        out_path = save_validation_report(self.settings, query_id, report)

        print(
            f"AttributeValidatorAgent finished for query_id={query_id}. "
            f"Valid={report.is_valid}. Issues={len(report.issues)}. "
            f"Output: {out_path}"
        )

        return report
