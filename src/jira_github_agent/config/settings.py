from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

def load_env() -> None:
    load_dotenv()

def must_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(
            f"Missing env var: {name}\n"
            f"Fix: set it in your shell or create a .env file (see .env.example)."
        )
    return v

@dataclass(frozen=True)
class Settings:
    # Jira
    jira_base_url: str
    jira_email: str
    jira_api_token: str

    # GitHub
    github_owner: str
    github_repo: str
    github_token: str
    git_author_name: str
    git_author_email: str

    # Runtime
    workdir: Path
    default_branch: str
    test_command: str

def get_settings() -> Settings:
    load_env()
    return Settings(
        jira_base_url=must_env("JIRA_BASE_URL").rstrip("/"),
        jira_email=must_env("JIRA_EMAIL"),
        jira_api_token=must_env("JIRA_API_TOKEN"),
        github_owner=must_env("GITHUB_OWNER"),
        github_repo=must_env("GITHUB_REPO"),
        github_token=must_env("GITHUB_TOKEN"),
        git_author_name=os.getenv("GIT_AUTHOR_NAME", "JiraBot"),
        git_author_email=os.getenv("GIT_AUTHOR_EMAIL", "leoccustodio@gmail.com"),
        workdir=Path(os.getenv("WORKDIR", "./workdir")).resolve(),
        default_branch=os.getenv("DEFAULT_BRANCH", "main"),
        test_command=os.getenv("TEST_COMMAND", "pytest -q"),
    )
