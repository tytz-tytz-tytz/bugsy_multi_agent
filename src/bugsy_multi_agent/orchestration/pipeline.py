from __future__ import annotations

from typing import List

from bugsy_multi_agent.agents.ontology_retriever_agent import (
    OntologyRAGRetrieverAgent,
)
from bugsy_multi_agent.agents.attribute_generator_agent import (
    AttributeGeneratorAgent,
)
from bugsy_multi_agent.agents.attribute_validator_agent import (
    AttributeValidatorAgent,
)
from bugsy_multi_agent.agents.attribute_coverage_checker_agent import (
    AttributeCoverageCheckerAgent,
)
from bugsy_multi_agent.agents.scenario_generator_agent import (
    ScenarioGeneratorAgent,
)
from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.models.attribute import Attribute
from bugsy_multi_agent.models.reports import (
    ValidationReport,
    AttributeCoverageReport,
)
from bugsy_multi_agent.models.scenario import Scenario
from bugsy_multi_agent.models.testing_context import TestingContext


class Pipeline:
    """
    End-to-end пайплайн.

    Сейчас реализованы шаги:
    1) OntologyRAG Retriever Agent -> TestingContext
    2) Attribute Generator Agent -> список Attribute
    3) Attribute Validator Agent -> ValidationReport
    4) Attribute Coverage Checker -> AttributeCoverageReport
    5) Scenario Generator Agent -> список Scenario
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.ensure_dirs()

        self.ontology_agent = OntologyRAGRetrieverAgent(settings=self.settings)
        self.attribute_generator = AttributeGeneratorAgent(settings=self.settings)
        self.attribute_validator = AttributeValidatorAgent(settings=self.settings)
        self.attribute_coverage_checker = AttributeCoverageCheckerAgent(
            settings=self.settings
        )
        self.scenario_generator = ScenarioGeneratorAgent(settings=self.settings)

    # ---------- отдельные шаги ----------

    def run_ontology_retriever(self, query_id: str) -> TestingContext:
        return self.ontology_agent.run(query_id)

    def run_attribute_generator(self, query_id: str) -> List[Attribute]:
        return self.attribute_generator.run(query_id)

    def run_attribute_validator(self, query_id: str) -> ValidationReport:
        return self.attribute_validator.run(query_id)

    def run_attribute_coverage_checker(
        self, query_id: str
    ) -> AttributeCoverageReport:
        return self.attribute_coverage_checker.run(query_id)

    def run_scenario_generator(self, query_id: str) -> List[Scenario]:
        return self.scenario_generator.run(query_id)

    # ---------- полный пайплайн ----------

    def run_full_pipeline(self, query_id: str) -> None:
        """
        Полный пайплайн:

        - нормализация контекста
        - генерация атрибутов
        - валидация атрибутов
        - отчёт по покрытию атрибутами
        - генерация сценариев
        """
        testing_context = self.run_ontology_retriever(query_id)
        print("---- OntologyRAG Retriever step done ----")
        print(f"Core passages: {len(testing_context.core_passages)}")
        print(f"Supporting passages: {len(testing_context.supporting_passages)}")

        attributes = self.run_attribute_generator(query_id)
        print("---- Attribute Generator step done ----")
        print(f"Attributes generated: {len(attributes)}")

        validation_report = self.run_attribute_validator(query_id)
        print("---- Attribute Validator step done ----")
        print(validation_report.summary)

        coverage_report = self.run_attribute_coverage_checker(query_id)
        print("---- Attribute Coverage Checker step done ----")
        print(coverage_report.summary)

        scenarios = self.run_scenario_generator(query_id)
        print("---- Scenario Generator step done ----")
        print(f"Scenarios generated: {len(scenarios)}")
