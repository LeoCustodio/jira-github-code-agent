# Chapter 02 — Installing Python, uv, and the Developer Environment

## Learning objectives

By the end of this chapter, you will be able to:

- Install and verify Python.
- Understand the role of virtual environments.
- Use `uv` for modern Python project management.
- Explain why dependency isolation matters.
- Create a repeatable beginner project structure.

## Why this matters

A surprising number of Python problems are not language problems. They are environment problems.

Common issues include:

- using the wrong Python version,
- installing packages globally,
- mixing dependencies between projects,
- running code with a different interpreter than expected,
- not pinning dependencies,
- not having reproducible setup instructions.

A Principal Engineer should care about this because environment inconsistency creates team friction, CI failures, deployment bugs, and onboarding delays.

## Python versions

Python evolves continuously. This course targets modern Python, ideally Python 3.13 or newer.

Check your version:

```bash
python --version
python3 --version
```

On some systems, `python` points to Python 2 or does not exist. On others, `python3` is the correct command. In professional projects, tools like `uv`, `pyenv`, containers, or CI images should make the version explicit.

## Interpreters

Python code is executed by an interpreter. The most common implementation is CPython.

When people say "Python", they usually mean:

- the Python language specification,
- the standard library,
- and CPython, the reference implementation.

Other implementations exist, such as PyPy, but CPython is the default assumption for most production systems.

## Virtual environments

A virtual environment isolates dependencies for one project.

Without isolation, installing one package version for Project A can break Project B.

Create a virtual environment with the standard library:

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

After activation:

```bash
python --version
pip --version
```

## uv

`uv` is a modern Python package and project manager. It can replace several older workflows involving `pip`, `venv`, and parts of `pip-tools` or Poetry.

A typical project can be created with:

```bash
uv init my-python-project
cd my-python-project
uv add pytest ruff mypy
uv run pytest
```

`uv run` executes commands inside the project environment.

## Minimal project structure

A simple beginner project:

```text
my_project/
├── pyproject.toml
├── README.md
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── main.py
└── tests/
    └── test_main.py
```

This structure keeps application code under `src/`, which avoids accidental imports from the current working directory during tests.

## First program

Create `src/my_project/main.py`:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(greet("Python"))
```

Run it:

```bash
uv run python src/my_project/main.py
```

Expected output:

```text
Hello, Python!
```

## First test

Create `tests/test_main.py`:

```python
from my_project.main import greet


def test_greet() -> None:
    assert greet("Leo") == "Hello, Leo!"
```

Run:

```bash
uv run pytest
```

## The `if __name__ == "__main__"` guard

This line means: execute the block only when the file is run directly, not when imported.

Example:

```python
print(__name__)
```

When run directly:

```text
__main__
```

When imported from another module, `__name__` becomes the module name.

This guard prevents import side effects.

## pyproject.toml

Modern Python projects use `pyproject.toml` to define metadata and tool configuration.

Example:

```toml
[project]
name = "my-python-project"
version = "0.1.0"
requires-python = ">=3.13"

dependencies = []

[dependency-groups]
dev = [
    "pytest",
    "ruff",
    "mypy",
]

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Best practices

- Use one virtual environment per project.
- Commit `pyproject.toml`.
- Commit lock files when your workflow creates them.
- Avoid global package installation.
- Use `src/` layout for packages.
- Run tests through the same tool the team uses in CI.
- Document setup commands in README.

## Anti-patterns

- Installing dependencies with `sudo pip install`.
- Mixing system Python and project Python.
- Relying on packages installed on your machine but not declared in the project.
- Running scripts from random folders without understanding import paths.
- Not specifying Python version expectations.

## Exercises

### Exercise 1

Create a new Python project using `uv` with this structure:

```text
hello_course/
├── pyproject.toml
├── src/hello_course/main.py
└── tests/test_main.py
```

### Exercise 2

Implement a function:

```python
def add(left: int, right: int) -> int:
    ...
```

Write tests for it.

### Exercise 3

Run `python -c "import sys; print(sys.executable)"` inside and outside your virtual environment. Compare the output.

## Solutions

### Solution 1

```bash
uv init hello_course
cd hello_course
mkdir -p src/hello_course tests
```

### Solution 2

```python
def add(left: int, right: int) -> int:
    return left + right
```

Test:

```python
from hello_course.main import add


def test_add() -> None:
    assert add(2, 3) == 5
```

### Solution 3

The virtual environment should point to an interpreter inside `.venv`. Outside the environment, it points to your system or user-level Python installation.

## Quiz

1. Why should dependencies not be installed globally?
2. What problem does a virtual environment solve?
3. What is the purpose of `pyproject.toml`?
4. Why is the `src/` layout useful?
5. What does `if __name__ == "__main__"` do?

## Interview questions

1. How would you standardize Python tooling across a team?
2. What causes "works on my machine" issues in Python projects?
3. How do virtual environments interact with CI/CD?
4. What is the difference between Python the language and CPython?

## Summary

Professional Python begins with reproducible tooling. Before writing complex code, establish the interpreter version, virtual environment, package manager, project structure, test runner, and formatting tools. Good environment discipline prevents many future bugs.
