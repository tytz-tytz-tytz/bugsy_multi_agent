from __future__ import annotations

import json
from typing import Any, Dict


def _format_section_candidates(raw: Dict[str, Any]) -> str:
    """
    Превращает section_candidates из raw JSON OntologyRAG в удобочитаемый текст.
    В LLM-промпт отдаём только нужные поля.
    """
    sections = raw.get("section_candidates", [])
    lines = []
    for idx, sec in enumerate(sections, start=1):
        section_id = sec.get("section_id", f"sec_{idx}")
        title = sec.get("title", "")
        score = sec.get("score", 0)
        text = sec.get("text", "")

        lines.append(
            f"[#{idx}] section_id={section_id} score={score}\n"
            f"TITLE: {title}\n"
            f"TEXT:\n{text}\n"
            f"--- END SECTION #{idx} ---"
        )

    if not lines:
        return "NO SECTION CANDIDATES PROVIDED."

    return "\n\n".join(lines)


def build_ontology_retriever_prompt(
    raw_context: Dict[str, Any],
    query_override: str | None = None,
) -> str:
    """
    Собирает промпт для OntologyRAGRetrieverAgent.

    query_override позволяет подменить текст запроса
    (например, взять его из data/queries.json).
    """
    query = (query_override or raw_context.get("query", "")).strip()
    sections_text = _format_section_candidates(raw_context)

    output_schema_description = json.dumps(
        {
            "query": "string (исходный запрос пользователя)",
            "focus_summary": "string (очень короткое резюме, 2-3 предложения, что именно нужно протестировать)",
            "core_passages": [
                {
                    "section_id": "string",
                    "title": "string",
                    "role": "core",
                    "importance": "high | medium | low",
                    "summary": "string (краткое содержание, 3-5 предложений)",
                }
            ],
            "supporting_passages": [
                {
                    "section_id": "string",
                    "title": "string",
                    "role": "supporting",
                    "importance": "high | medium | low",
                    "summary": "string",
                }
            ],
            "discarded_sections": ["section_id", "..."],
            "domain_entities": ["EntityName", "..."],
            "hints_for_tests": [
                "Короткая подсказка для тестов, основанная на документации"
            ],
        },
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
Ты выступаешь в роли OntologyRAG Retriever Agent для системы тест-дизайна.

Тебе дан:
1) исходный запрос пользователя (query),
2) список отобранных секций документации (section_candidates) с оценкой релевантности.

Твоя задача:
- понять, что именно нужно тестировать по этому запросу;
- отобрать только те секции, которые реально помогают понять требования к системе;
- разделить их на:
  - core_passages: ключевые секции, на которых обязательно надо базировать тесты;
  - supporting_passages: дополнительные, уточняющие детали, примеры, крайние случаи;
  - discarded_sections: явный шум (аудит, маркетинг, нерелевантные описания);
- для каждого core/supporting passage сделать короткое summary для тест-дизайнера;
- выделить domain_entities: важные сущности домена (объекты системы, роли, статусы);
- сформулировать hints_for_tests: подсказки, какие аспекты логики и ограничений надо покрыть тестами.

Особое внимание:
- Убирай маркетинговый текст, общие описания компании, аудит, SLA, не связанные с логикой работы системы.
- Если секция описывает поведение, условия, ограничения, сценарии, статусы, роли — это, скорее всего, core или supporting.
- Не придумывай содержимое секций, опирайся только на переданный текст.

Формат вывода:
- Строго один JSON-объект без пояснений и комментариев.
- Структура должна соответствовать описанию ниже (TestingContext):

{output_schema_description}

Исходный запрос пользователя (query):
\"\"\"{query}\"\"\"

Секции документации (section_candidates), которые нужно проанализировать:

{sections_text}

Напомню: верни только JSON-объект TestingContext, без дополнительного текста до или после JSON.
"""
    return prompt.strip()
