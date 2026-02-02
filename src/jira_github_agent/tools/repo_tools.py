from __future__ import annotations
import os, re, shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from jira_github_agent.runtime.shell import run, run_capture

class CloneInput(BaseModel):
    owner: str
    repo: str
    token: str
    workdir: str
    default_branch: str = "main"

class CreateBranchInput(BaseModel):
    repo_dir: str
    branch_name: str

class ListFilesInput(BaseModel):
    repo_dir: str
    max_files: int = 250
    include_patterns: List[str] = Field(default_factory=lambda: ["*.py","*.md","pyproject.toml","requirements.txt"])

class ReadFilesInput(BaseModel):
    repo_dir: str
    paths: List[str]

class ApplyPatchInput(BaseModel):
    repo_dir: str
    unified_diff: str

class RunTestsInput(BaseModel):
    repo_dir: str
    command: str = "pytest -q"

class CommitPushInput(BaseModel):
    repo_dir: str
    branch_name: str
    message: str
    author_name: str
    author_email: str

def build_repo_tools():
    @tool("github_clone_repo", args_schema=CloneInput)
    def github_clone_repo(owner: str, repo: str, token: str, workdir: str, default_branch: str="main") -> Dict[str, Any]:
        """Clone the github project repository"""
        work = Path(workdir).resolve()
        repo_dir = (work / f"{owner}-{repo}").resolve()
        work.mkdir(parents=True, exist_ok=True)
        if repo_dir.exists():
            shutil.rmtree(repo_dir)

        clone_url = f"https://{token}:x-oauth-basic@github.com/{owner}/{repo}.git"
        run(["git","clone","--branch",default_branch,clone_url,str(repo_dir)])
        return {"ok": True, "repo_dir": str(repo_dir)}

    @tool("git_create_branch", args_schema=CreateBranchInput)
    def git_create_branch(repo_dir: str, branch_name: str) -> Dict[str, Any]:
        """Create github branch"""
        rd = Path(repo_dir)
        run(["git","checkout","-b",branch_name], cwd=rd)
        return {"ok": True}

    @tool("repo_list_files", args_schema=ListFilesInput)
    def repo_list_files(repo_dir: str, max_files: int=250, include_patterns: Optional[List[str]]=None) -> Dict[str, Any]:
        """Read all files in the github project repository and list it"""
        rd = Path(repo_dir)
        pats = include_patterns or ["*.py"]
        files: List[str] = []
        for pat in pats:
            for p in rd.rglob(pat):
                if p.is_file() and ".git" not in p.parts:
                    files.append(str(p.relative_to(rd)))
        files = sorted(files)[:max_files]
        return {"files": files, "count": len(files)}

    @tool("repo_read_files", args_schema=ReadFilesInput)
    def repo_read_files(repo_dir: str, paths: List[str]) -> Dict[str, Any]:
        """Read the files on the specified github project repository"""
        rd = Path(repo_dir)
        out: Dict[str, str] = {}
        for rel in paths[:25]:
            p = (rd / rel).resolve()
            if rd not in p.parents:
                continue
            if p.exists() and p.is_file():
                out[rel] = p.read_text(encoding="utf-8", errors="replace")[:20000]
        return {"files": out}

    @tool("apply_patch", args_schema=ApplyPatchInput)
    def apply_patch(repo_dir: str, unified_diff: str) -> Dict[str, Any]:
        """Apply project patchs"""
        rd = Path(repo_dir)
        patch_path = rd / ".agent.patch"
        patch_path.write_text(unified_diff, encoding="utf-8")
        run(["git","apply","--whitespace=fix",str(patch_path)], cwd=rd)
        return {"ok": True}

    @tool("run_tests", args_schema=RunTestsInput)
    def run_tests(repo_dir: str, command: str="pytest -q") -> Dict[str, Any]:
        """Run Project Tests"""
        rd = Path(repo_dir)
        return run_capture(command, cwd=rd)

    @tool("git_commit_push", args_schema=CommitPushInput)
    def git_commit_push(repo_dir: str, branch_name: str, message: str, author_name: str, author_email: str) -> Dict[str, Any]:
        """Create the git commit description and command and push it to the branch created"""
        rd = Path(repo_dir)
        run(["git","config","user.name",author_name], cwd=rd)
        run(["git","config","user.email",author_email], cwd=rd)
        run(["git","add","-A"], cwd=rd)
        run(["git","commit","-m",message], cwd=rd)
        run(["git","push","-u","origin",branch_name], cwd=rd)
        return {"ok": True}

    return [github_clone_repo, git_create_branch, repo_list_files, repo_read_files, apply_patch, run_tests, git_commit_push]
