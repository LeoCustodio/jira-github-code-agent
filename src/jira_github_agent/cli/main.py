from __future__ import annotations
import os
from langchain_core.messages import HumanMessage
from jira_github_agent.graphs.jira_to_pr_graph import app

def main() -> None:
    issue_key = os.getenv("JIRA_ISSUE_KEY", "").strip()
    if not issue_key:
        raise SystemExit("Set JIRA_ISSUE_KEY=ABC-123")

    print("[cli] invoking graph...")  # debug

    result = app.invoke({
        "messages": [HumanMessage(content=f"Implement Jira ticket {issue_key} and open a PR.")],
        "issue_key": issue_key,
        "repo_dir": "",
        "branch_name": "",
        "pr_url": None,
        "jira_summary": "",
        "jira_description": "",
        "last_test_output": None,
    })

    print("[cli] done")
    print("PR URL:", result.get("pr_url"))

if __name__ == "__main__":
    main()
