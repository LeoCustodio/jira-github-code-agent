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
        r = self.session.post(url, json={"title":"Amazing new feature","body":"Please pull these awesome changes in!","head":"jira/SCRUM-5","base":"main"}, timeout=self.timeout_s)
        if r.status_code >= 400:
            # GitHub tells you exactly what field is wrong (e.g., head/base invalid)
            raise RuntimeError(f"GitHub API error {r.status_code}: {r.text}")
        return r.json()
