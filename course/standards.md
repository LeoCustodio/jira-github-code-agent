# Course Standards

## Writing standard

Every chapter must be written as a self-study technical book chapter, not as short notes.

Each chapter must include:

1. Learning objectives
2. Why the topic matters
3. Conceptual explanation
4. Python-specific behavior
5. CPython/runtime details when relevant
6. Runnable code examples
7. Expected output
8. Common mistakes
9. Production guidance
10. Exercises
11. Solutions
12. Quiz
13. Interview questions
14. Summary

## Code standard

All Python code should target modern Python.

Recommended defaults:

```toml
[project]
requires-python = ">=3.13"

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Style rules

- Prefer explicit names over clever abbreviations.
- Prefer small functions with clear responsibilities.
- Use type hints in production examples.
- Keep beginner examples readable, then gradually introduce advanced techniques.
- Separate domain logic from infrastructure.
- Avoid global mutable state unless teaching why it is dangerous.
- Include failure paths, not only happy paths.

## Exercise standard

Each exercise should include:

- Problem statement
- Constraints
- Input examples
- Expected output
- Hints
- Solution
- Discussion of trade-offs

## Project standard

Each project should include:

- Problem context
- Requirements
- Non-functional requirements
- Architecture diagram
- Milestones
- Tests
- Extension ideas
- Production considerations

## Commit standard

Use clear commit messages:

```text
Add chapter 01 Python philosophy
Add beginner exercises for functions
Add solutions for collection exercises
```
