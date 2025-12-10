from __future__ import annotations

import json
from typing import Any


def extract_json_from_text(text: str) -> Any:
    """
    Пытается вытащить JSON-объект или массив из произвольного текста.

    Стратегия:
    - срезаем markdown-кодовые блоки ```...```, если есть;
    - ищем первый символ '{' или '[' и последний '}' или ']';
    - парсим через json.loads.
    """
    s = text.strip()

    # Убираем кодовые блоки ```...```
    if s.startswith("```"):
        parts = s.split("```")
        # parts: ["", "json\n{...}", "" ] или ["", "{...}", ""]
        for part in parts:
            part = part.strip()
            if part and not part.startswith("```"):
                s = part
                break

    # Ищем первый символ начала JSON
    first_idx = len(s)
    for ch in ("{", "["):
        i = s.find(ch)
        if i != -1 and i < first_idx:
            first_idx = i
    if first_idx == len(s):
        # Не нашли вообще
        raise ValueError("No JSON start character found in LLM response")

    s = s[first_idx:]

    # Ищем последний символ конца JSON
    last_obj = s.rfind("}")
    last_arr = s.rfind("]")
    last_idx = max(last_obj, last_arr)
    if last_idx == -1:
        raise ValueError("No JSON end character found in LLM response")

    s = s[: last_idx + 1]

    return json.loads(s)
