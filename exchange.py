from __future__ import annotations
import json, os, logging
from datetime import datetime
from typing import Dict, Optional

import requests
from PySide6.QtCore import QSettings

from variables import DEFAULT_CURRENCY_RATES

_LOG = logging.getLogger(__name__)


class RateProvider:
    ORG, APP = "MintBalance", "FinanceApp"
    _KEY_RATES = "fx_rates"
    _KEY_DATE  = "fx_date"

    _URL_XHOST = "https://api.exchangerate.host/latest"
    _PARAMS_X  = {"base": "USD", "symbols": "RUB,EUR"}
    _ENV_KEY   = "XRATE_KEY"

    _URL_FALL  = "https://open.er-api.com/v6/latest/USD"

    def __init__(self) -> None:
        self._s = QSettings(self.ORG, self.APP)
        self._rates: Dict[str, float] = (
            self._load_cached() or DEFAULT_CURRENCY_RATES.copy()
        )
        self._update_once_per_day()

    def __getitem__(self, code: str) -> float:
        return self._rates[code]

    def all(self) -> Dict[str, float]:
        return self._rates.copy()

    def _load_cached(self) -> Optional[Dict[str, float]]:
        try:
            date_iso = self._s.value(self._KEY_DATE, "")
            if date_iso and datetime.fromisoformat(date_iso).date() == datetime.utcnow().date():
                return json.loads(self._s.value(self._KEY_RATES, ""))
        except Exception:
            pass
        return None

    def _save_cache(self):
        self._s.setValue(self._KEY_RATES, json.dumps(self._rates))
        self._s.setValue(self._KEY_DATE, datetime.utcnow().isoformat())
        self._s.sync()

    def _fetch_xhost(self) -> Dict[str, float]:
        """Первый источник — exchangerate.host (apilayer)."""
        params = self._PARAMS_X.copy()
        key = os.getenv(self._ENV_KEY) or self._s.value(self._ENV_KEY, "")
        if key:
            params["access_key"] = key

        resp = requests.get(self._URL_XHOST, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success", True):
            raise RuntimeError(f"xhost error: {data.get('error')}")

        rates = data["rates"]
        usd_rub = rates["RUB"]
        usd_eur = rates["EUR"]
        return {
            "RUB": 1.0,
            "USD": usd_rub,
            "EUR": usd_rub / usd_eur,
        }

    def _fetch_open_er(self) -> Dict[str, float]:
        resp = requests.get(self._URL_FALL, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        if data.get("result") != "success":
            raise RuntimeError("open.er-api.com: bad response")

        rates = data["rates"]
        usd_rub = rates["RUB"]
        usd_eur = rates["EUR"]
        return {
            "RUB": 1.0,
            "USD": usd_rub,
            "EUR": usd_rub / usd_eur,
        }

    def _update_once_per_day(self):
        if self._load_cached():
            return

        try:
            self._rates = self._fetch_xhost()
            _LOG.info("Курсы обновлены через exchangerate.host")
        except Exception as e_x:
            _LOG.warning("exchangerate.host недоступен (%s) — пытаемся fallback", e_x)
            try:
                self._rates = self._fetch_open_er()
                _LOG.info("Курсы обновлены через open.er-api.com")
            except Exception as e_f:
                _LOG.error("оба провайдера недоступны (%s) — остаёмся на кэше", e_f)

        finally:
            self._save_cache()
