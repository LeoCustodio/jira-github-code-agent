from __future__ import annotations

import os
import re
import shutil
import stat
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import tool

from jira_github_agent.runtime.shell import run, run_capture
from urllib.parse import quote

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
    include_patterns: List[str] = Field(default_factory=lambda: ["*.py", "*.md", "pyproject.toml", "requirements.txt"])


class ReadFilesInput(BaseModel):
    repo_dir: str
    paths: List[str]


class ApplyPatchInput(BaseModel):
    repo_dir: str
    unified_diff: str


class WriteFilesInput(BaseModel):
    repo_dir: str
    files: Dict[str, str]  # { "relative/path": "content" }


class DeletePathsInput(BaseModel):
    repo_dir: str
    paths: List[str]  # relative paths to delete (file or directory)


class RunTestsInput(BaseModel):
    repo_dir: str
    command: str = "pytest -q"


class CommitPushInput(BaseModel):
    repo_dir: str
    branch_name: str
    message: str
    author_name: str
    author_email: str
    owner: str
    repo: str
    token: str


def _safe_repo_path(repo_dir: Path, rel_path: str) -> Path:
    """
    Prevent path traversal. Only allow repo-relative paths.
    """
    rel_path = rel_path.replace("\\", "/").lstrip("/")
    if not rel_path or rel_path.startswith("../") or "/../" in rel_path:
        raise ValueError(f"Unsafe path: {rel_path}")

    full = (repo_dir / rel_path).resolve()
    root = repo_dir.resolve()
    if root not in full.parents and full != root:
        raise ValueError(f"Path escapes repo: {rel_path}")
    return full


def _make_writable(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass


def _rmtree_force(path: Path) -> None:
    """
    Robust recursive delete for Windows (handles read-only).
    """
    def onerror(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
        except Exception:
            pass
        # small delay helps when antivirus/FS is still releasing handles
        time.sleep(0.05)
        func(p)

    if path.exists():
        shutil.rmtree(path, onerror=onerror)


def build_repo_tools():
    @tool("github_clone_repo", args_schema=CloneInput)
    def github_clone_repo(owner: str, repo: str, token: str, workdir: str, default_branch: str = "main") -> Dict[str, Any]:
        """Clone the github project repository"""
        work = Path(workdir).resolve()
        repo_dir = (work / f"{owner}-{repo}").resolve()
        work.mkdir(parents=True, exist_ok=True)

        if repo_dir.exists():
            _rmtree_force(repo_dir)

        clone_url = f"https://{token}:x-oauth-basic@github.com/{owner}/{repo}.git"
        run(["git", "clone", "--branch", default_branch, clone_url, str(repo_dir)])
        return {"ok": True, "repo_dir": str(repo_dir)}

    @tool("git_create_branch", args_schema=CreateBranchInput)
    def git_create_branch(repo_dir: str, branch_name: str) -> Dict[str, Any]:
        """Create github branch"""
        rd = Path(repo_dir)
        run(["git", "checkout", "-b", branch_name], cwd=rd)
        return {"ok": True}

    @tool("repo_list_files", args_schema=ListFilesInput)
    def repo_list_files(repo_dir: str, max_files: int = 250, include_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Read all files in the github project repository and list it"""
        rd = Path(repo_dir)
        pats = include_patterns or ["*.py"]
        files: List[str] = []
        for pat in pats:
            for p in rd.rglob(pat):
                if p.is_file() and ".git" not in p.parts:
                    files.append(str(p.relative_to(rd)).replace("\\", "/"))
        files = sorted(files)[:max_files]
        return {"files": files, "count": len(files)}

    @tool("repo_read_files", args_schema=ReadFilesInput)
    def repo_read_files(repo_dir: str, paths: List[str]) -> Dict[str, Any]:
        """Read the files on the specified github project repository"""
        rd = Path(repo_dir)
        out: Dict[str, str] = {}
        for rel in paths[:25]:
            rel = rel.replace("\\", "/")
            p = _safe_repo_path(rd, rel)
            if p.exists() and p.is_file():
                out[rel] = p.read_text(encoding="utf-8", errors="replace")[:20000]
        return {"files": out}

    # -----------------------------
    # NEW: patchless write tool
    # -----------------------------
    @tool("repo_write_files", args_schema=WriteFilesInput)
    def repo_write_files(repo_dir: str, files: Dict[str, str]) -> Dict[str, Any]:
        """Write/update files in the repository (repo-relative paths)."""
        rd = Path(repo_dir)
        written: List[str] = []
        for rel, content in list(files.items())[:50]:
            rel = rel.replace("\\", "/").lstrip("/")
            p = _safe_repo_path(rd, rel)
            p.parent.mkdir(parents=True, exist_ok=True)

            if p.exists():
                _make_writable(p)

            # normalize CRLF -> LF for consistency
            content = str(content).replace("\r\n", "\n").replace("\r", "\n")
            p.write_text(content, encoding="utf-8", newline="\n")
            written.append(rel)
        return {"ok": True, "written": written, "count": len(written)}

    # -----------------------------
    # NEW: patchless delete tool
    # -----------------------------
    @tool("repo_delete_paths", args_schema=DeletePathsInput)
    def repo_delete_paths(repo_dir: str, paths: List[str]) -> Dict[str, Any]:
        """Delete files/directories in the repository (repo-relative paths)."""
        rd = Path(repo_dir)
        deleted: List[str] = []
        for rel in paths[:50]:
            rel = rel.replace("\\", "/").lstrip("/")
            p = _safe_repo_path(rd, rel)
            if not p.exists():
                continue

            if p.is_dir():
                _rmtree_force(p)
            else:
                _make_writable(p)
                p.unlink()
            deleted.append(rel)

        return {"ok": True, "deleted": deleted, "count": len(deleted)}

    # Keep apply_patch for backwards-compat, but you won't need it.
    @tool("apply_patch", args_schema=ApplyPatchInput)
    def apply_patch(repo_dir: str, unified_diff: str) -> Dict[str, Any]:
        """Apply project patches (legacy)."""
        rd = Path(repo_dir)
        patch_path = rd / ".agent.patch"
        patch_path.write_text(unified_diff, encoding="utf-8", newline="\n")
        run(["git", "apply", "--whitespace=fix", str(patch_path)], cwd=rd)
        return {"ok": True}

    @tool("run_tests", args_schema=RunTestsInput)
    def run_tests(repo_dir: str, command: str = "pytest -q") -> Dict[str, Any]:
        """Run Project Tests"""
        rd = Path(repo_dir)
        return run_capture(command, cwd=rd)



    @tool("git_commit_push", args_schema=CommitPushInput)
    def git_commit_push( 
        repo_dir: str,
        branch_name: str,
        message: str,
        author_name: str,
        author_email: str,
        owner: str,
        repo: str,
        token: str,
    ) -> Dict[str, Any]:
        """Create commit and push to github repository"""
        rd = Path(repo_dir)
        token = token.strip()
        token_enc = quote(token, safe="")

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        # x-access-token é o padrão correto para GitHub Actions/Tokens
        remote_url = f"https://x-access-token:{token_enc}@github.com/{owner}/{repo}.git"

        try:
            # Configuração local para não afetar o sistema global
            run(["git", "config", "user.name", author_name], cwd=rd, env=env)
            run(["git", "config", "user.email", author_email], cwd=rd, env=env)

            run(["git", "add", "-A"], cwd=rd, env=env)
            
            # Commit com check=False para tratar o "nothing to commit" manualmente
            run(["git", "commit", "-m", message], cwd=rd, env=env)
            # if cp.returncode != 0 and "nothing to commit" not in cp.stdout.lower():
            #     return {"ok": False, "error": cp.stderr}

            # Push: check=True é essencial aqui
            run(
                [
                    "git", 
                    "-c", "credential.helper=", 
                    "-c", "core.askpass=true", 
                    "push", "-u", remote_url, f"HEAD:{branch_name}" # HEAD garante que você empurra o commit atual
                ],
                cwd=rd,
                env=env
            )
            return {"ok": True, "message": "Push realizado com sucesso"}

        # except run.CalledProcessError as e:
        #     # Remove o token da mensagem de erro por segurança
        #     error_msg = str(e.stderr).replace(token, "***").replace(token_enc, "***")
        #     return {"ok": False, "error": error_msg}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return [
        github_clone_repo,
        git_create_branch,
        repo_list_files,
        repo_read_files,
        repo_write_files,     # NEW
        repo_delete_paths,    # NEW
        apply_patch,          # legacy
        run_tests,
        git_commit_push,
    ]