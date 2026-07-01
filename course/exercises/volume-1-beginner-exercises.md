# Volume 1 — Beginner Exercises

## Chapter 01 — Why Python Matters

### Exercise 01

List five systems where Python would be a good fit. For each one, explain why.

### Exercise 02

List three systems where Python might not be the best primary language. Explain the trade-off.

## Chapter 02 — Installation and Tooling

### Exercise 03

Create a project with `uv`, add `pytest`, and write one passing test.

### Exercise 04

Print the active Python executable from inside and outside a virtual environment.

Expected command:

```bash
python -c "import sys; print(sys.executable)"
```

## Chapter 03 — Values, Objects, Names, and References

### Exercise 05

Predict the output:

```python
users = ["Ana", "Bruno"]
admins = users
admins.append("Carla")
print(users)
```

### Exercise 06

Fix this function:

```python
def append_log(message: str, logs: list[str] = []) -> list[str]:
    logs.append(message)
    return logs
```

### Exercise 07

Write a function that receives a list of integers and returns a new list with only even numbers, without mutating the original list.

## Review Exercises

### Exercise 08

Explain the difference between `==` and `is` using your own example.

### Exercise 09

Explain why this code is dangerous:

```python
def create_order(items: list[str] = []) -> dict[str, list[str]]:
    return {"items": items}
```

### Exercise 10

Create a small command-line program that asks for a name and prints a greeting.
