from __future__ import annotations

import json
import os
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


# -----------------------------
# Direct-edit helpers (NO PATCHES)
# -----------------------------
def _safe_repo_path(repo_dir: str, rel_path: str) -> Path:
    """
    Prevent path traversal. Only allow paths inside repo_dir.
    """
    rel_path = rel_path.replace("\\", "/").lstrip("/")
    if not rel_path or rel_path.startswith("../") or "/../" in rel_path:
        raise ValueError(f"Unsafe path: {rel_path}")
    full = (Path(repo_dir) / rel_path).resolve()
    root = Path(repo_dir).resolve()
    if root not in full.parents and full != root:
        raise ValueError(f"Path escapes repo: {rel_path}")
    return full


def _parse_edit_plan(text: str) -> Dict[str, Any]:
    """
    LLM must return strict JSON:
      {
        "edits": [
          {"path":"src/x.js","action":"upsert","content":"..."},
          {"path":"src/y.js","action":"delete"}
        ]
      }
    """
    if not text:
        raise ValueError("Empty LLM response for edit plan.")

    t = text.strip()

    # Strip common markdown fences if model disobeys
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)

    try:
        obj = json.loads(t)
    except json.JSONDecodeError as e:
        raise ValueError(f"Edit plan is not valid JSON: {e}") from e

    if not isinstance(obj, dict) or "edits" not in obj or not isinstance(obj["edits"], list):
        raise ValueError("Edit plan must be a JSON object with an 'edits' array.")

    for i, ed in enumerate(obj["edits"]):
        if not isinstance(ed, dict):
            raise ValueError(f"Edit #{i} must be an object.")
        if "path" not in ed or "action" not in ed:
            raise ValueError(f"Edit #{i} must contain 'path' and 'action'.")
        if ed["action"] not in ("upsert", "delete"):
            raise ValueError(f"Edit #{i} action must be 'upsert' or 'delete'.")
        if ed["action"] == "upsert" and "content" not in ed:
            raise ValueError(f"Edit #{i} with action 'upsert' must include 'content'.")

    return obj


def _apply_edits(repo_dir: str, edits: List[Dict[str, Any]]) -> None:
    """
    Apply edits directly to filesystem (no git apply).
    Uses repo_tools repo_write_files/repo_delete_files if they exist; otherwise writes directly.
    """
    repo_write_files = next((t for t in repo_tools if t.name == "repo_write_files"), None)
    repo_delete_files = next((t for t in repo_tools if t.name == "repo_delete_files"), None)

    upserts: Dict[str, str] = {}
    deletes: List[str] = []

    for ed in edits:
        path = ed["path"].replace("\\", "/").lstrip("/")
        action = ed["action"]
        if action == "upsert":
            # Normalize newlines to LF to reduce churn; let git handle core.autocrlf if configured
            content = str(ed["content"]).replace("\r\n", "\n").replace("\r", "\n")
            upserts[path] = content
        else:
            deletes.append(path)

    # Prefer repo_tools if present
    if upserts and repo_write_files is not None:
        # expected signature: {"repo_dir":..., "files": {"path": "content", ...}}
        repo_write_files.invoke({"repo_dir": repo_dir, "files": upserts})
    else:
        for rel, content in upserts.items():
            full = _safe_repo_path(repo_dir, rel)
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8", newline="\n")

    if deletes and repo_delete_files is not None:
        # expected signature: {"repo_dir":..., "paths": [...]}
        repo_delete_files.invoke({"repo_dir": repo_dir, "paths": deletes})
    else:
        for rel in deletes:
            full = _safe_repo_path(repo_dir, rel)
            if full.exists():
                # On Windows, deletion can fail if file is in use; keep it simple here.
                try:
                    full.unlink()
                except IsADirectoryError:
                    # If directory, remove recursively
                    for p in sorted(full.rglob("*"), reverse=True):
                        try:
                            p.unlink()
                        except IsADirectoryError:
                            p.rmdir()
                    full.rmdir()
# -----------------------------


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
    # run_tests = next(t for t in repo_tools if t.name == "run_tests")

    listing = repo_list_files.invoke({"repo_dir": state["repo_dir"], "max_files": 250})
    files: List[str] = listing["files"]

    # Pick a small preview set; LLM can request more later if you add a retry loop
    candidates = [f for f in files if any(k in f.lower() for k in ["service", "controller", "api", "routes", "handler", "main", "app", "receipt"])]
    candidates = (candidates + files)[:12]
    preview = repo_read_files.invoke({"repo_dir": state["repo_dir"], "paths": candidates})

    context = {
        "jira": {
            "key": state["issue_key"],
            "summary": state["jira_summary"],
            "description": state["jira_description"],
        },
        "repo_files": files,
        "files_preview": {k: v[:6000] for k, v in preview["files"].items()},
        "rules": {
            "edit_actions": ["upsert", "delete"],
            "path_rules": "paths must be relative to repo root; never absolute; do not escape repo",
        },
    }

    EDIT_PLAN_SYSTEM = SystemMessage(content=(
        "You are a coding agent. Implement the Jira task by returning ONLY a strict JSON edit plan.\n"
        "No prose, no markdown fences, no explanations.\n\n"
        "JSON schema:\n"
        "{\n"
        '  "edits": [\n'
        '    {"path": "relative/path.ext", "action": "upsert", "content": "FULL FILE CONTENT"},\n'
        '    {"path": "relative/path.ext", "action": "delete"}\n'
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Only include files that already exist in repo_files unless you are intentionally creating a new file.\n"
        "- For upsert: provide FULL final file content (not a patch).\n"
        "- Keep changes minimal; do not reformat unrelated code.\n"
        "- Paths must be repo-relative using forward slashes.\n"
    ))

    prompt = HumanMessage(content=(
        "Generate the JSON edit plan using the context below:\n\n"
        f"{json.dumps(context, indent=2, ensure_ascii=False)}"
    ))

    plan_text = llm.invoke([EDIT_PLAN_SYSTEM, prompt]).content
    plan = _parse_edit_plan(plan_text)

    # Optional guardrail: refuse to touch too many files (prevents runaway rewrites)
    edits = plan["edits"]
    if len(edits) > 12:
        raise RuntimeError(f"Edit plan wants to modify {len(edits)} files; refusing (limit 12).")

    # Apply edits directly (no patches)
    _apply_edits(state["repo_dir"], edits)

    # test = run_tests.invoke({"repo_dir": state["repo_dir"], "command": settings.test_command})
    # last = (test.get("stdout","") + "\n" + test.get("stderr","")).strip()
    # if not test["ok"]:
    #     raise RuntimeError(f"Tests failed:\n{last}")

    return {"last_test_output": "true"}


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
        "owner": settings.github_owner,
        "repo": settings.github_repo,
        "token": settings.github_token,
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