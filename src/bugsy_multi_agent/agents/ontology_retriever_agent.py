from __future__ import annotations

import json
from typing import Any

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.json_io import read_json, write_json
from bugsy_multi_agent.data_access.query_mapping import get_query_text
from bugsy_multi_agent.llm.client import DeepSeekLLMClient
from bugsy_multi_agent.llm.json_utils import extract_json_from_text
from bugsy_multi_agent.llm.prompts_ontology import build_ontology_retriever_prompt
from bugsy_multi_agent.models.testing_context import TestingContext, Passage
from bugsy_multi_agent.orchestration.agent_base import AgentBase


class OntologyRAGRetrieverAgent(AgentBase):
    """
    Агент, который берет сырые выходы OntologyRAG (data/contexts/{query_id}.json)
    и превращает их в стандартизированный TestingContext.

    Теперь умеет звать DeepSeek; при проблемах с JSON откатывается на эвристику.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings=settings)
        # Инициализируем клиента один раз на агент
        self.llm_client = DeepSeekLLMClient()

    def _load_raw_context(self, query_id: str) -> dict:
        path = self.settings.contexts_dir / f"{query_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Raw context file not found: {path}")
        return read_json(path)

    def _build_testing_context_heuristic(self, raw: dict) -> TestingContext:
        query = raw.get("query", "")
        section_candidates = raw.get("section_candidates", [])

        core_passages: list[Passage] = []
        supporting_passages: list[Passage] = []

        for idx, section in enumerate(section_candidates):
            role = "core" if idx == 0 else "supporting"
            importance = "high" if idx == 0 else "medium"

            passage = Passage(
                section_id=section.get("section_id", f"sec_{idx}"),
                title=section.get("title", ""),
                role=role,
                importance=importance,
                summary=section.get("text", "")[:500],
            )

            if role == "core":
                core_passages.append(passage)
            else:
                supporting_passages.append(passage)

        focus_summary = (
            f"Auto-generated focus summary for query: {query}. "
            f"Core passages count: {len(core_passages)}."
        )

        return TestingContext(
            query=query,
            focus_summary=focus_summary,
            core_passages=core_passages,
            supporting_passages=supporting_passages,
            discarded_sections=[],
            domain_entities=[],
            hints_for_tests=[],
        )

    def _build_testing_context_with_llm(
        self,
        raw: dict,
        display_query: str,
    ) -> TestingContext:
        prompt = build_ontology_retriever_prompt(
            raw_context=raw,
            query_override=display_query,
        )

        response_text = self.llm_client.generate(prompt)
        data = extract_json_from_text(response_text)

        # Ожидаем один JSON-объект
        if not isinstance(data, dict):
            raise ValueError("LLM response is not a JSON object for TestingContext")

        return TestingContext.from_dict(data)

    def run(self, query_id: str) -> TestingContext:
        """
        Главная точка входа.

        - читает сырой контекст,
        - пробует получить TestingContext через LLM,
        - при ошибке откатывается на эвристику,
        - сохраняет результат в JSON.
        """
        raw = self._load_raw_context(query_id)

        display_query = get_query_text(
            self.settings,
            query_id,
            fallback=raw.get("query", ""),
        )

        try:
            testing_context = self._build_testing_context_with_llm(
                raw=raw,
                display_query=display_query,
            )
            used_llm = True
        except Exception as e:
            print(
                f"OntologyRAGRetrieverAgent: LLM failed for query_id={query_id}: {e}. "
                f"Falling back to heuristic."
            )
            testing_context = self._build_testing_context_heuristic(raw)
            used_llm = False

        out_path = self.settings.ontology_retriever_dir / f"{query_id}.json"
        write_json(out_path, testing_context.to_dict())

        print(
            f"OntologyRAGRetrieverAgent finished for query_id={query_id}. "
            f"used_llm={used_llm}. Output: {out_path}"
        )

        return testing_context
