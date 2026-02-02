from __future__ import annotations
from typing import Optional, Dict, Any
import requests
from requests.auth import HTTPBasicAuth

class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str, timeout_s: int = 30):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get(self, path: str, params: Optional[dict] = None) -> Dict[str, Any]:
        r = self.session.get(self._url(path), params=params, auth=self.auth, timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, body: dict) -> Dict[str, Any]:
        r = self.session.post(self._url(path), json=body, auth=self.auth, timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()
