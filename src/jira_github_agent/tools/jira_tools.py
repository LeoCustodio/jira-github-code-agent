from __future__ import annotations
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from jira_github_agent.runtime.adf import adf_to_text
from jira_github_agent.clients.jira_client import JiraClient

class JiraGetIssueInput(BaseModel):
    issue_key: str = Field(..., description="Jira issue key, e.g. ABC-123")

def build_jira_tools(jira: JiraClient):
    @tool("jira_get_issue", args_schema=JiraGetIssueInput)
    def jira_get_issue(issue_key: str) -> Dict[str, Any]:
        """Get the first ticket in the 'to do' column and return the description        """
        data = jira.get(f"/rest/api/3/issue/{issue_key}", params={"fields": "summary,description"})
        f = data.get("fields", {})
        desc_adf = f.get("description")
        return {
            "key": data.get("key"),
            "summary": f.get("summary", ""),
            "description_adf": desc_adf,
            "description_text": adf_to_text(desc_adf),
        }

    return [jira_get_issue]
