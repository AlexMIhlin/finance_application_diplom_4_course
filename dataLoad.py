from __future__ import annotations
import json
import importlib
from typing import Any, Dict, List

import pandas as pd
from PySide6.QtCore import QSettings


class SettingsManager:
    ORG, APP = "MintBalance", "FinanceApp"
    _DEFAULTS = {"lang": "ru", "theme": "light", "currency": "RUB"}

    def __init__(self) -> None:
        self._s = QSettings(self.ORG, self.APP)

    def get(self, key: str) -> Any:
        return self._s.value(key, self._DEFAULTS[key])

    def set(self, key: str, value: Any) -> None:
        self._s.setValue(key, value)

    def all(self) -> Dict[str, Any]:
        return {k: self.get(k) for k in self._DEFAULTS}

    def sync(self) -> None:
        self._s.sync()

    def get_json(self, key: str, default: Any = None) -> Any:
        val = self._s.value(key, None)
        return default if val is None else json.loads(val)

    def set_json(self, key: str, value: Any) -> None:
        self._s.setValue(key, json.dumps(value))


def export_to_excel(rows: List[dict[str, str]], path: str) -> None:
    if not rows:
        raise ValueError("No data to export")


    engine = None
    if importlib.util.find_spec("openpyxl") is None:
        if importlib.util.find_spec("xlsxwriter") is not None:
            engine = "xlsxwriter"
        else:
            raise ImportError(
                "Для экспорта нужен пакет «openpyxl» или «xlsxwriter».\n"
                "Установите один из них, например:\n"
                "   pip install openpyxl"
            )

    pd.DataFrame(rows).to_excel(path, index=False, engine=engine)
