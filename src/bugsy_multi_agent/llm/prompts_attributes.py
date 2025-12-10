from __future__ import annotations

from typing import List

from bugsy_multi_agent.models.testing_context import TestingContext, Passage


def _format_passages(passages: List[Passage], label: str) -> str:
    """
    Форматирует список Passages в удобный для LLM текстовый блок.
    """
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


def build_attribute_generator_prompt(
    ctx: TestingContext,
    query_override: str | None = None,
) -> str:
    """
    Собирает промпт для AttributeGeneratorAgent.

    query_override позволяет подменить текст запроса
    (например, взять его из data/queries.json).
    """
    core_text = _format_passages(ctx.core_passages, "CORE PASSAGES")
    supp_text = _format_passages(ctx.supporting_passages, "SUPPORTING PASSAGES")

    query_text = (query_override or ctx.query).strip()

    domain_entities_text = (
        "\n".join(f"- {e}" for e in ctx.domain_entities)
        if ctx.domain_entities
        else "нет явных сущностей"
    )
    hints_text = (
        "\n".join(f"- {h}" for h in ctx.hints_for_tests)
        if ctx.hints_for_tests
        else "нет подсказок, опирайся на тексты секций"
    )

    prompt = f"""
Ты выступаешь в роли Attribute Generator Agent в системе тест-дизайна.

Тебе дан TestingContext по запросу пользователя.

Запрос пользователя (query):
\"\"\"{query_text}\"\"\"

Фокус-резюме (focus_summary):
\"\"\"{ctx.focus_summary}\"\"\"

CORE PASSAGES и SUPPORTING PASSAGES описывают ключевые требования и поведение системы:

{core_text}

{supp_text}

domain_entities:
{domain_entities_text}

hints_for_tests:
{hints_text}

Твоя задача:
- на основе core_passages, supporting_passages, domain_entities и hints_for_tests
  сгенерировать набор атомарных тестовых атрибутов (требований).

Требования к атрибутам:
- каждый атрибут описывает одно конкретное правило/требование/ограничение;
- у каждого атрибута:
  - id: уникальный строковый идентификатор, формат вроде "EVT-001", "EVT-002", ...
  - name: короткое человеческое название требования;
  - type: один из "business_rule", "functional", "ui", "negative";
  - priority: один из "P1", "P2", "P3";
  - description: понятное описание требования;
  - positive_example: пример корректного поведения/входных данных;
  - negative_example: пример некорректного поведения/входных данных или нарушения правила;
  - source_section_ids: массив section_id тех секций, из которых явным образом следует этот атрибут;
  - source_quotes: массив коротких цитат из документации, подтверждающих этот атрибут.

Формат вывода:
- строго один JSON-массив объектов Attribute.
- без обёртки вида {{ "attributes": [...] }}, только список:
  [{{...}}, {{...}}, ...]

Схема одного элемента массива:
{{
  "id": "EVT-001",
  "name": "string",
  "type": "business_rule | functional | ui | negative",
  "priority": "P1 | P2 | P3",
  "description": "string",
  "positive_example": "string",
  "negative_example": "string",
  "source_section_ids": ["sec_1", "sec_2"],
  "source_quotes": ["цитата из документации", "..."]
}}

Важно:
- Не выдумывай требования, которых нет в документации.
- Если информация не очевидна, формулируй атрибут так, чтобы он оставался честным и опирался на текст.
- Старайся не делать дублирующих атрибутов с одинаковым смыслом.

Напомню: верни только JSON-массив объектов Attribute, без дополнительного текста до или после.
"""
    return prompt.strip()
