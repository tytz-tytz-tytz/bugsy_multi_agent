from __future__ import annotations

from typing import List

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.attribute_store import load_attributes
from bugsy_multi_agent.data_access.json_io import read_json
from bugsy_multi_agent.data_access.query_mapping import get_query_text
from bugsy_multi_agent.data_access.scenario_store import save_scenarios
from bugsy_multi_agent.llm.client import DeepSeekLLMClient
from bugsy_multi_agent.llm.json_utils import extract_json_from_text
from bugsy_multi_agent.llm.prompts_scenarios import build_scenario_generator_prompt
from bugsy_multi_agent.models.attribute import Attribute
from bugsy_multi_agent.models.scenario import Scenario
from bugsy_multi_agent.models.testing_context import TestingContext
from bugsy_multi_agent.orchestration.agent_base import AgentBase


class ScenarioGeneratorAgent(AgentBase):
    """
    Агент, который на основе списка атрибутов генерирует тестовые сценарии.

    Порядок:
    - пробуем LLM (DeepSeek),
    - при ошибке откатываемся на заглушку: один сценарий на атрибут.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings=settings)
        self.llm_client = DeepSeekLLMClient()

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

    def _generate_scenarios_stub(
        self,
        ctx: TestingContext,
        attributes: List[Attribute],
    ) -> List[Scenario]:
        scenarios: List[Scenario] = []

        for idx, attr in enumerate(attributes, start=1):
            scenario_id = f"SCN-{idx:03d}"

            title = f"Проверка требования: {attr.name}"

            steps = [
                "Подготовить систему к тестированию согласно документации.",
                (
                    "Настроить исходные данные и окружение так, чтобы "
                    "можно было проверить данное требование."
                ),
                (
                    "Выполнить действия, описанные в атрибуте "
                    f"и его позитивном примере: {attr.positive_example}"
                ),
            ]

            expected_result = (
                "Система ведёт себя в соответствии с требованием: "
                f"{attr.description}"
            )

            scenario = Scenario(
                id=scenario_id,
                title=title,
                steps=steps,
                expected_result=expected_result,
                attributes_covered=[attr.id],
            )
            scenarios.append(scenario)

        return scenarios

    def _generate_scenarios_with_llm(
        self,
        ctx: TestingContext,
        attributes: List[Attribute],
        display_query: str,
    ) -> List[Scenario]:
        prompt = build_scenario_generator_prompt(
            ctx=ctx,
            attributes=attributes,
            query_override=display_query,
        )
        response_text = self.llm_client.generate(prompt)
        data = extract_json_from_text(response_text)

        if not isinstance(data, list):
            raise ValueError("LLM response is not a JSON array for Scenario list")

        scenarios: List[Scenario] = []
        for obj in data:
            if not isinstance(obj, dict):
                raise ValueError("Scenario item is not a JSON object")
            scenarios.append(Scenario.from_dict(obj))

        return scenarios

    def run(self, query_id: str) -> List[Scenario]:
        ctx = self._load_testing_context(query_id)
        attributes = self._load_attributes(query_id)

        display_query = get_query_text(
            self.settings,
            query_id,
            fallback=ctx.query,
        )

        try:
            scenarios = self._generate_scenarios_with_llm(
                ctx=ctx,
                attributes=attributes,
                display_query=display_query,
            )
            used_llm = True
        except Exception as e:
            print(
                f"ScenarioGeneratorAgent: LLM failed for query_id={query_id}: {e}. "
                f"Falling back to stub."
            )
            scenarios = self._generate_scenarios_stub(ctx, attributes)
            used_llm = False

        out_path = save_scenarios(self.settings, query_id, scenarios)

        print(
            f"ScenarioGeneratorAgent finished for query_id={query_id}. "
            f"Generated {len(scenarios)} scenarios. used_llm={used_llm}. "
            f"Output: {out_path}"
        )

        return scenarios
