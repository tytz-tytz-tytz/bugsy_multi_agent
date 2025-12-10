from __future__ import annotations

from typing import List

from bugsy_multi_agent.models.testing_context import TestingContext, Passage
from bugsy_multi_agent.models.attribute import Attribute


def _format_passages(passages: List[Passage], label: str) -> str:
    if not passages:
        return f"{label}: []"

    lines = [f"{label}:"]
    for idx, p in enumerate(passages, start=1):
        lines.append(
            f"[{idx}] section_id={p.section_id}\n"
            f"TITLE: {p.title}\n"
            f"SUMMARY: {p.summary}\n"
        )
    return "\n".join(lines)


def _format_attributes(attrs: List[Attribute]) -> str:
    if not attrs:
        return "ATTRIBUTES: []"

    lines = ["ATTRIBUTES:"]
    for idx, a in enumerate(attrs, start=1):
        lines.append(
            f"[{idx}] id={a.id}\n"
            f"NAME: {a.name}\n"
            f"TYPE: {a.type}, PRIORITY: {a.priority}\n"
            f"DESCRIPTION: {a.description}\n"
            f"POSITIVE: {a.positive_example}\n"
            f"NEGATIVE: {a.negative_example}\n"
            f"SOURCE SECTIONS: {', '.join(a.source_section_ids)}\n"
        )
    return "\n".join(lines)


def build_scenario_generator_prompt(
    ctx: TestingContext,
    attributes: List[Attribute],
    query_override: str | None = None,
) -> str:
    """
    Собирает промпт для ScenarioGeneratorAgent.

    query_override позволяет подменить текст запроса
    (например, взять его из data/queries.json).
    """
    core_text = _format_passages(ctx.core_passages, "CORE PASSAGES")
    supp_text = _format_passages(ctx.supporting_passages, "SUPPORTING PASSAGES")
    attrs_text = _format_attributes(attributes)

    query_text = (query_override or ctx.query).strip()

    prompt = f"""
Ты выступаешь в роли Scenario Generator Agent в системе тест-дизайна.

Тебе дано:
- TestingContext по запросу пользователя,
- список атомарных атрибутов (требований), которые нужно покрыть сценариями.

Запрос пользователя (query):
\"\"\"{query_text}\"\"\"

Фокус-резюме (focus_summary):
\"\"\"{ctx.focus_summary}\"\"\"

CORE PASSAGES и SUPPORTING PASSAGES:

{core_text}

{supp_text}

Список атрибутов:

{attrs_text}

Твоя задача:
- сгенерировать набор тестовых сценариев, которые стратегически покрывают атрибуты;
- один сценарий может покрывать несколько атрибутов;
- избегай тупого 1:1 (один атрибут = один сценарий), старайся группировать логически связанные атрибуты.

Требования к сценарию:
- id: уникальный строковый идентификатор, формат вроде "SCN-001", "SCN-002", ...
- title: короткое осмысленное название сценария;
- steps: массив текстовых шагов, понятных тестировщику, в логическом порядке;
- expected_result: чётко сформулированный ожидаемый результат;
- attributes_covered: массив id атрибутов, которые покрывает этот сценарий.

Формат вывода:
- строго один JSON-массив объектов Scenario.
- без обёртки вида {{ "scenarios": [...] }}, только список:
  [{{...}}, {{...}}, ...]

Схема одного элемента массива:
{{
  "id": "SCN-001",
  "title": "string",
  "steps": ["шаг 1", "шаг 2", "..."],
  "expected_result": "string",
  "attributes_covered": ["EVT-001", "EVT-002"]
}}

Важно:
- Шаги должны быть реалистичными и соответствовать документации.
- expected_result должен проверять, что система ведёт себя в соответствии с атрибутами из attributes_covered.
- Не выдумывай поведение, которого нет в документации.

Напомню: верни только JSON-массив объектов Scenario, без дополнительного текста до или после.
"""
    return prompt.strip()
