# Volume 1 — Beginner Quiz

## Chapter 01

1. Why is Python useful for Principal Engineers?
2. Name three systems where Python is a strong fit.
3. Name two systems where Python may not be the best choice.
4. What does "readability counts" mean in code review?

## Chapter 02

1. What is a virtual environment?
2. Why should dependencies not be installed globally?
3. What is `pyproject.toml`?
4. What does `uv run` do?
5. Why is the `src/` layout useful?

## Chapter 03

1. What are the three properties every Python object has?
2. What is the difference between equality and identity?
3. Why is `is None` preferred over `== None`?
4. Why are mutable default arguments dangerous?
5. What is the difference between shallow copy and deep copy?

## Practical Quiz

Given this code:

```python
def add_role(role: str, roles: list[str] = []) -> list[str]:
    roles.append(role)
    return roles

print(add_role("admin"))
print(add_role("owner"))
```

1. What is the output?
2. Why does it happen?
3. How would you fix it?
