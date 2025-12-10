from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    """
    Читает JSON-файл и возвращает Python-объект.
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any, *, indent: int = 2) -> None:
    """
    Записывает Python-объект в JSON-файл.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def list_json_files(directory: Path) -> list[Path]:
    """
    Возвращает список JSON-файлов в директории.
    """
    if not directory.exists():
        return []
    return sorted(p for p in directory.iterdir() if p.suffix == ".json")
