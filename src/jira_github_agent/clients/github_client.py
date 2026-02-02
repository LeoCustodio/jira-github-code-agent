from __future__ import annotations
from typing import Dict, Any
import requests

class GitHubClient:
    def __init__(self, token: str, timeout_s: int = 30):
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def post(self, url: str, body: dict) -> Dict[str, Any]:
        r = self.session.post(url, json=body, timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()
