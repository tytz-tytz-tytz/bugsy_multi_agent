from __future__ import annotations

from typing import List

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.attribute_store import save_attributes
from bugsy_multi_agent.data_access.json_io import read_json
from bugsy_multi_agent.data_access.query_mapping import get_query_text
from bugsy_multi_agent.llm.client import DeepSeekLLMClient
from bugsy_multi_agent.llm.json_utils import extract_json_from_text
from bugsy_multi_agent.llm.prompts_attributes import build_attribute_generator_prompt
from bugsy_multi_agent.models.attribute import Attribute
from bugsy_multi_agent.models.testing_context import TestingContext, Passage
from bugsy_multi_agent.orchestration.agent_base import AgentBase


class AttributeGeneratorAgent(AgentBase):
    """
    Агент, который на основе TestingContext генерирует набор тестовых атрибутов.

    Порядок:
    - пробуем LLM (DeepSeek);
    - при ошибках откатываемся на локальную заглушку.
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

    def _generate_attributes_stub(self, ctx: TestingContext) -> List[Attribute]:
        attributes: List[Attribute] = []

        if ctx.core_passages:
            core: Passage = ctx.core_passages[0]

            attributes.append(
                Attribute(
                    id="EVT-001",
                    name=f"{core.title or 'Core behaviour'} – basic flow",
                    type="functional",
                    priority="P1",
                    description=(
                        f"Основное ожидаемое поведение, описанное в секции "
                        f"{core.section_id}: {core.title}."
                    ),
                    positive_example=(
                        "Пользователь выполняет стандартные действия, "
                        "описанные в секции, и получает ожидаемый результат."
                    ),
                    negative_example=(
                        "Пользователь нарушает обязательное условие из секции, "
                        "и система корректно отклоняет операцию."
                    ),
                    source_section_ids=[core.section_id],
                    source_quotes=[core.summary[:300]],
                )
            )

            attributes.append(
                Attribute(
                    id="EVT-002",
                    name=f"{core.title or 'Core behaviour'} – invalid input",
                    type="negative",
                    priority="P2",
                    description=(
                        f"Проверка поведения при некорректных входных данных "
                        f"для сценария из секции {core.section_id}."
                    ),
                    positive_example=(
                        "Пользователь вводит гранично корректные данные, "
                        "и система принимает их без ошибок."
                    ),
                    negative_example=(
                        "Пользователь вводит явно некорректные данные "
                        "(пустые поля, неверные значения), и система возвращает "
                        "понятное сообщение об ошибке."
                    ),
                    source_section_ids=[core.section_id],
                    source_quotes=[core.summary[:300]],
                )
            )
        else:
            attributes.append(
                Attribute(
                    id="EVT-001",
                    name="Basic behaviour – generic",
                    type="functional",
                    priority="P2",
                    description="Общее ожидаемое поведение, вытекающее из фокуса запроса.",
                    positive_example=(
                        "Система ведёт себя в соответствии с основной "
                        "формулировкой focus_summary."
                    ),
                    negative_example=(
                        "Система нарушает основное требование, описанное "
                        "во focus_summary."
                    ),
                    source_section_ids=[],
                    source_quotes=[ctx.focus_summary[:300]],
                )
            )

        return attributes

    def _generate_attributes_with_llm(
        self,
        ctx: TestingContext,
        display_query: str,
    ) -> List[Attribute]:
        prompt = build_attribute_generator_prompt(
            ctx,
            query_override=display_query,
        )
        response_text = self.llm_client.generate(prompt)
        data = extract_json_from_text(response_text)

        if not isinstance(data, list):
            raise ValueError("LLM response is not a JSON array for Attribute list")

        attributes: List[Attribute] = []
        for obj in data:
            if not isinstance(obj, dict):
                raise ValueError("Attribute item is not a JSON object")
            attributes.append(Attribute.from_dict(obj))

        return attributes

    def run(self, query_id: str) -> List[Attribute]:
        ctx = self._load_testing_context(query_id)

        display_query = get_query_text(
            self.settings,
            query_id,
            fallback=ctx.query,
        )

        try:
            attributes = self._generate_attributes_with_llm(ctx, display_query)
            used_llm = True
        except Exception as e:
            print(
                f"AttributeGeneratorAgent: LLM failed for query_id={query_id}: {e}. "
                f"Falling back to stub."
            )
            attributes = self._generate_attributes_stub(ctx)
            used_llm = False

        out_path = save_attributes(self.settings, query_id, attributes)

        print(
            f"AttributeGeneratorAgent finished for query_id={query_id}. "
            f"Generated {len(attributes)} attributes. used_llm={used_llm}. "
            f"Output: {out_path}"
        )

        return attributes
