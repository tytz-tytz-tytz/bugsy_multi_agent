from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.json_io import read_json


def _get_queries_path(settings: Settings) -> Path:
    """
    Путь к общему файлу с описаниями запросов.
    Формат: data/queries.json
    """
    return settings.data_dir / "queries.json"


def load_query_mapping(settings: Settings) -> Dict[str, Dict[str, Any]]:
    """
    Загружает весь маппинг query_id -> информация о запросе.

    Формат в файле:
    {
      "query_1": {
        "title": "Редактирование существующего события",
        "user_query": "Как редактируется существующее пользовательское событие?"
      },
      ...
    }
    """
    path = _get_queries_path(settings)
    if not path.exists():
        return {}
    raw = read_json(path)
    if not isinstance(raw, dict):
        raise ValueError(f"queries.json must contain a JSON object, got: {type(raw)}")
    return raw  # type: ignore[return-value]


def get_query_text(
    settings: Settings,
    query_id: str,
    fallback: Optional[str] = None,
) -> str:
    """
    Возвращает человекочитаемый текст запроса для query_id.

    Приоритет:
    1) data/queries.json: entry["user_query"]
    2) data/queries.json: entry["title"]
    3) fallback (например, raw_context['query'])
    4) сам query_id, если больше вообще ничего нет
    """
    mapping = load_query_mapping(settings)
    entry = mapping.get(query_id) or {}

    user_query = entry.get("user_query")
    title = entry.get("title")

    if isinstance(user_query, str) and user_query.strip():
        return user_query.strip()
    if isinstance(title, str) and title.strip():
        return title.strip()
    if fallback and fallback.strip():
        return fallback.strip()
    return query_id
