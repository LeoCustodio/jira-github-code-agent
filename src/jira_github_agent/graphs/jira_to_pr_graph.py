from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, TypedDict, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from jira_github_agent.config.settings import get_settings
from jira_github_agent.clients.jira_client import JiraClient
from jira_github_agent.clients.github_client import GitHubClient
from jira_github_agent.tools.jira_tools import build_jira_tools
from jira_github_agent.tools.repo_tools import build_repo_tools
from jira_github_agent.tools.github_tools import build_github_tools


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    issue_key: str
    repo_dir: str
    branch_name: str
    pr_url: Optional[str]
    jira_summary: str
    jira_description: str
    last_test_output: Optional[str]


def load_prompt_text(name: str) -> str:
    here = Path(__file__).resolve().parents[1]
    return (here / "prompts" / name).read_text(encoding="utf-8")


settings = get_settings()
jira = JiraClient(settings.jira_base_url, settings.jira_email, settings.jira_api_token)
gh = GitHubClient(settings.github_token)

jira_tools = build_jira_tools(jira)
repo_tools = build_repo_tools()
github_tools = build_github_tools(gh)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

DIFF_ONLY_SYSTEM = SystemMessage(content=load_prompt_text("diff_only_system.txt"))


def node_fetch_jira(state: AgentState) -> Dict[str, Any]:
    jira_get_issue = jira_tools[0]
    data = jira_get_issue.invoke({"issue_key": state["issue_key"]})
    return {
        "jira_summary": data["summary"],
        "jira_description": data["description_text"] or "",
        "messages": [SystemMessage(content=f"Loaded Jira {data['key']}: {data['summary']}")],
    }


def node_prepare_repo(state: AgentState) -> Dict[str, Any]:
    github_clone_repo = next(t for t in repo_tools if t.name == "github_clone_repo")
    git_create_branch = next(t for t in repo_tools if t.name == "git_create_branch")

    clone = github_clone_repo.invoke({
        "owner": settings.github_owner,
        "repo": settings.github_repo,
        "token": settings.github_token,
        "workdir": str(settings.workdir),
        "default_branch": settings.default_branch,
    })
    repo_dir = clone["repo_dir"]

    safe_key = re.sub(r"[^a-zA-Z0-9._-]+", "-", state["issue_key"])
    branch_name = f"jira/{safe_key}"
    git_create_branch.invoke({"repo_dir": repo_dir, "branch_name": branch_name})

    return {"repo_dir": repo_dir, "branch_name": branch_name}


def node_generate_apply_test(state: AgentState) -> Dict[str, Any]:
    repo_list_files = next(t for t in repo_tools if t.name == "repo_list_files")
    repo_read_files = next(t for t in repo_tools if t.name == "repo_read_files")
    apply_patch = next(t for t in repo_tools if t.name == "apply_patch")
    run_tests = next(t for t in repo_tools if t.name == "run_tests")

    listing = repo_list_files.invoke({"repo_dir": state["repo_dir"], "max_files": 250})
    files: List[str] = listing["files"]

    candidates = [f for f in files if any(k in f.lower() for k in ["service","controller","api","routes","handler","main","app"])]
    candidates = (candidates + files)[:10]
    preview = repo_read_files.invoke({"repo_dir": state["repo_dir"], "paths": candidates})

    context = {
        "jira": {"key": state["issue_key"], "summary": state["jira_summary"], "description": state["jira_description"]},
        "repo_files": files,
        "files_preview": {k: v[:4000] for k, v in preview["files"].items()},
    }

    prompt = HumanMessage(content="Implement the Jira task. Return ONLY a unified diff.\n\n" + json.dumps(context, indent=2, ensure_ascii=False))
    patch = llm.invoke([DIFF_ONLY_SYSTEM, prompt]).content

    apply_patch.invoke({"repo_dir": state["repo_dir"], "unified_diff": patch})

    test = run_tests.invoke({"repo_dir": state["repo_dir"], "command": settings.test_command})
    last = (test.get("stdout","") + "\n" + test.get("stderr","")).strip()

    if not test["ok"]:
        # Minimal: fail fast. Later you can add a retry loop node.
        raise RuntimeError(f"Tests failed:\n{last}")

    return {"last_test_output": last[-20000:]}


def node_commit_and_pr(state: AgentState) -> Dict[str, Any]:
    git_commit_push = next(t for t in repo_tools if t.name == "git_commit_push")
    github_create_pr = github_tools[0]

    title = f"{state['issue_key']}: {state['jira_summary']}"
    git_commit_push.invoke({
        "repo_dir": state["repo_dir"],
        "branch_name": state["branch_name"],
        "message": title,
        "author_name": settings.git_author_name,
        "author_email": settings.git_author_email,
    })

    pr = github_create_pr.invoke({
        "owner": settings.github_owner,
        "repo": settings.github_repo,
        "head": state["branch_name"],
        "base": settings.default_branch,
        "title": title,
        "body": f"Implements {state['issue_key']}\n\n{state['jira_description'][:1500]}",
    })
    return {"pr_url": pr["url"]}


graph = StateGraph(AgentState)
graph.add_node("fetch_jira", node_fetch_jira)
graph.add_node("prepare_repo", node_prepare_repo)
graph.add_node("generate_apply_test", node_generate_apply_test)
graph.add_node("commit_and_pr", node_commit_and_pr)

graph.set_entry_point("fetch_jira")
graph.add_edge("fetch_jira", "prepare_repo")
graph.add_edge("prepare_repo", "generate_apply_test")
graph.add_edge("generate_apply_test", "commit_and_pr")
graph.add_edge("commit_and_pr", END)

app = graph.compile()
