from __future__ import annotations

from pathlib import Path

from bugsy_multi_agent.config.settings import Settings
from bugsy_multi_agent.data_access.json_io import read_json, write_json
from bugsy_multi_agent.models.reports import AttributeCoverageReport


def get_attribute_coverage_path(settings: Settings, query_id: str) -> Path:
    """
    Путь к файлу отчёта покрытия атрибутами.
    Формат: attribute_coverage_{query_id}.json
    """
    filename = f"attribute_coverage_{query_id}.json"
    return settings.attribute_coverage_checker_dir / filename


def save_attribute_coverage_report(
    settings: Settings, query_id: str, report: AttributeCoverageReport
) -> Path:
    """
    Сохраняет AttributeCoverageReport в JSON.
    """
    path = get_attribute_coverage_path(settings, query_id)
    write_json(path, report.model_dump())
    return path


def load_attribute_coverage_report(
    settings: Settings, query_id: str
) -> AttributeCoverageReport:
    """
    Загружает AttributeCoverageReport из JSON.
    """
    path = get_attribute_coverage_path(settings, query_id)
    raw = read_json(path)
    return AttributeCoverageReport.model_validate(raw)
