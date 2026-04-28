from abc import ABC

import requests


class BaseCollector(ABC):
    HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    TIMEOUT = 15

    def _get(self, url: str, params: dict = None, headers: dict = None):
        try:
            r = requests.get(url, headers=headers or self.HEADERS,
                             params=params, timeout=self.TIMEOUT)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def _get_list(self, url: str, params: dict = None, headers: dict = None):
        result = self._get(url, params, headers)
        return result if isinstance(result, list) else None

    def _get_text(self, url: str, params: dict = None) -> str:
        try:
            r = requests.get(url, headers=self.HEADERS, params=params, timeout=self.TIMEOUT)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        return ""
