from __future__ import annotations

from pathlib import Path

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.json_io import read_json, write_json
from bugsy_multi_agent.models.reports import ValidationReport


def get_validation_report_path(settings: Settings, query_id: str) -> Path:
    """
    Путь к файлу отчёта валидации атрибутов.
    Формат: attribute_validation_{query_id}.json
    """
    filename = f"attribute_validation_{query_id}.json"
    return settings.attribute_validator_dir / filename


def save_validation_report(
    settings: Settings, query_id: str, report: ValidationReport
) -> Path:
    """
    Сохраняет ValidationReport в JSON.
    """
    path = get_validation_report_path(settings, query_id)
    write_json(path, report.model_dump())
    return path


def load_validation_report(settings: Settings, query_id: str) -> ValidationReport:
    """
    Загружает ValidationReport из JSON.
    """
    path = get_validation_report_path(settings, query_id)
    raw = read_json(path)
    return ValidationReport.model_validate(raw)
