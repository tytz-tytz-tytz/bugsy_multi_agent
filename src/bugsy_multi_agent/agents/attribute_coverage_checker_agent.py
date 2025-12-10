from __future__ import annotations

from typing import List

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.attribute_store import load_attributes
from bugsy_multi_agent.data_access.attribute_coverage_store import (
    save_attribute_coverage_report,
)
from bugsy_multi_agent.data_access.json_io import read_json
from bugsy_multi_agent.models.attribute import Attribute
from bugsy_multi_agent.models.reports import (
    AttributeCoverageEntry,
    AttributeCoverageReport,
)
from bugsy_multi_agent.models.testing_context import TestingContext, Passage
from bugsy_multi_agent.orchestration.agent_base import AgentBase


class AttributeCoverageCheckerAgent(AgentBase):
    """
    Строит отчёт по покрытию core_passages атрибутами.
    Пока без domain_entities (их у нас ещё не генерят).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings=settings)

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

    def _build_passage_coverage(
        self, passages: List[Passage], attributes: List[Attribute]
    ) -> AttributeCoverageReport:
        covered: List[AttributeCoverageEntry] = []
        uncovered: List[AttributeCoverageEntry] = []

        for passage in passages:
            attr_ids_for_passage: list[str] = []
            for attr in attributes:
                if passage.section_id in attr.source_section_ids:
                    attr_ids_for_passage.append(attr.id)

            entry = AttributeCoverageEntry(
                entity_id=passage.section_id,
                entity_type="passage",
                description=passage.title or passage.summary[:200],
                attribute_ids=attr_ids_for_passage,
            )

            if attr_ids_for_passage:
                covered.append(entry)
            else:
                uncovered.append(entry)

        report = AttributeCoverageReport(
            query="",
            covered=covered,
            uncovered=uncovered,
            summary="",
        )

        return report

    def run(self, query_id: str) -> AttributeCoverageReport:
        """
        Строит отчёт по покрытию core_passages атрибутами
        и сохраняет его в JSON.
        """
        ctx = self._load_testing_context(query_id)
        attributes = self._load_attributes(query_id)

        base_report = self._build_passage_coverage(ctx.core_passages, attributes)
        base_report.query = ctx.query

        covered_count = len(base_report.covered)
        uncovered_count = len(base_report.uncovered)

        base_report.summary = (
            f"Core passages: {covered_count + uncovered_count}. "
            f"Covered: {covered_count}. Uncovered: {uncovered_count}."
        )

        out_path = save_attribute_coverage_report(
            self.settings,
            query_id,
            base_report,
        )

        print(
            f"AttributeCoverageCheckerAgent finished for query_id={query_id}. "
            f"Covered={covered_count}, uncovered={uncovered_count}. "
            f"Output: {out_path}"
        )

        return base_report
