from __future__ import annotations

from pathlib import Path
from typing import List

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.json_io import read_json, write_json
from bugsy_multi_agent.models.scenario import Scenario


def get_scenarios_path(settings: Settings, query_id: str) -> Path:
    """
    Возвращает путь к файлу со сценариями для указанного query_id.

    Формат файла: scenarios_{query_id}.json
    Пример: scenarios_query_1.json
    """
    filename = f"scenarios_{query_id}.json"
    return settings.scenario_generator_dir / filename


def save_scenarios(settings: Settings, query_id: str, scenarios: List[Scenario]) -> Path:
    """
    Сохраняет список сценариев в JSON-файл.

    По контракту это должен быть JSON-массив объектов Scenario.
    """
    path = get_scenarios_path(settings, query_id)
    data = [sc.to_dict() for sc in scenarios]
    write_json(path, data)
    return path


def load_scenarios(settings: Settings, query_id: str) -> List[Scenario]:
    """
    Загружает список сценариев из JSON-файла.
    """
    path = get_scenarios_path(settings, query_id)
    raw = read_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"Scenarios file {path} must contain a JSON array")
    return [Scenario.from_dict(item) for item in raw]
