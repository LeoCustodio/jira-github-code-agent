from __future__ import annotations
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from jira_github_agent.clients.github_client import GitHubClient

class CreatePrInput(BaseModel):
    owner: str
    repo: str
    head: str
    base: str = "main"
    title: str
    body: str = ""

def build_github_tools(gh: GitHubClient):
    @tool("github_create_pr", args_schema=CreatePrInput)
    def github_create_pr(owner: str, repo: str, head: str, base: str, title: str, body: str="") -> Dict[str, Any]:
        """Create Pull request in the github repository provided with the code generated"""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        resp = gh.post(url, {"title": title, "body": body, "head": head, "base": base, })
        return {"url": resp.get("html_url"), "number": resp.get("number")}

    return [github_create_pr]
