# Project 01 — CLI Task Manager

## Goal

Build a command-line task manager using beginner Python concepts.

This project reinforces:

- functions,
- lists and dictionaries,
- file handling,
- JSON serialization,
- command-line interaction,
- basic testing.

## Requirements

The application must support:

1. Add a task.
2. List all tasks.
3. Mark a task as done.
4. Delete a task.
5. Persist tasks to a JSON file.
6. Load tasks when the program starts.

## Data model

A task can be represented as a dictionary:

```python
task = {
    "id": 1,
    "title": "Study Python objects",
    "done": False,
}
```

Later in the course, this will be refactored into dataclasses and then into a clean architecture project.

## Suggested structure

```text
cli_task_manager/
├── pyproject.toml
├── src/
│   └── cli_task_manager/
│       ├── __init__.py
│       ├── main.py
│       ├── storage.py
│       └── tasks.py
└── tests/
    ├── test_tasks.py
    └── test_storage.py
```

## Milestone 1 — In-memory task operations

Implement:

```python
def add_task(tasks: list[dict[str, object]], title: str) -> dict[str, object]:
    ...


def list_tasks(tasks: list[dict[str, object]]) -> list[dict[str, object]]:
    ...


def complete_task(tasks: list[dict[str, object]], task_id: int) -> bool:
    ...


def delete_task(tasks: list[dict[str, object]], task_id: int) -> bool:
    ...
```

## Milestone 2 — Persistence

Implement:

```python
def load_tasks(path: str) -> list[dict[str, object]]:
    ...


def save_tasks(path: str, tasks: list[dict[str, object]]) -> None:
    ...
```

Use JSON.

## Milestone 3 — CLI menu

Example menu:

```text
1. Add task
2. List tasks
3. Complete task
4. Delete task
5. Exit
```

## Milestone 4 — Tests

Write tests for:

- adding a task,
- completing a task,
- deleting a task,
- saving and loading tasks.

## Stretch goals

- Add due dates.
- Add priorities.
- Add tags.
- Add search.
- Add command-line arguments using `argparse`.
- Add colored output.
- Convert dictionaries to dataclasses.

## Principal-level reflection

Even this simple project raises architecture questions:

- Should functions mutate input or return new state?
- Where should persistence live?
- How should errors be handled?
- How do we test file IO?
- What happens if the JSON file is corrupted?
- How do we migrate data format later?

Beginner projects are not only about syntax. They are opportunities to practice engineering judgment.
