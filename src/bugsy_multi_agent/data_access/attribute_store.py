from __future__ import annotations

from pathlib import Path
from typing import List

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.json_io import read_json, write_json
from bugsy_multi_agent.models.attribute import Attribute


def get_attributes_path(settings: Settings, query_id: str) -> Path:
    """
    Возвращает путь к файлу с атрибутами для указанного query_id.

    Формат файла: attributes_{query_id}.json
    Пример: attributes_query_1.json
    """
    filename = f"attributes_{query_id}.json"
    return settings.attribute_generator_dir / filename


def save_attributes(settings: Settings, query_id: str, attributes: List[Attribute]) -> Path:
    """
    Сохраняет список атрибутов в JSON-файл.

    ВАЖНО: по контракту это должен быть JSON-массив объектов Attribute.
    Без дополнительных обёрток.
    """
    path = get_attributes_path(settings, query_id)
    data = [attr.to_dict() for attr in attributes]
    write_json(path, data)
    return path


def load_attributes(settings: Settings, query_id: str) -> List[Attribute]:
    """
    Загружает список атрибутов из JSON-файла.
    """
    path = get_attributes_path(settings, query_id)
    raw = read_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"Attributes file {path} must contain a JSON array")
    return [Attribute.from_dict(item) for item in raw]
