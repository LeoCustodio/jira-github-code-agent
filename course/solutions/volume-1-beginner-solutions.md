# Volume 1 — Beginner Solutions

## Solution 01

Good Python fits:

1. Internal automation tool — Python is fast to write and has strong standard libraries.
2. ETL pipeline — Python integrates well with APIs, files, databases, and queues.
3. AI document processor — Python has the strongest AI and ML ecosystem.
4. Test automation framework — pytest and related tools are mature.
5. REST API for internal systems — FastAPI and Django are productive frameworks.

## Solution 02

Cases where Python may not be ideal:

1. Ultra-low-latency trading loop — runtime overhead and GC behavior may be unacceptable.
2. Embedded hard real-time firmware — Python runtime is usually too heavy.
3. CPU-heavy computation written as pure Python loops — may require native extensions, NumPy, Rust, or another language.

## Solution 03

```bash
uv init hello-python
cd hello-python
uv add --dev pytest
mkdir -p tests
```

Create `tests/test_example.py`:

```python
def test_truth() -> None:
    assert 1 + 1 == 2
```

Run:

```bash
uv run pytest
```

## Solution 04

```bash
python -c "import sys; print(sys.executable)"
```

Inside the virtual environment, the executable should point into `.venv`.

## Solution 05

```text
['Ana', 'Bruno', 'Carla']
```

`admins` and `users` reference the same list object.

## Solution 06

```python
def append_log(message: str, logs: list[str] | None = None) -> list[str]:
    if logs is None:
        logs = []
    logs.append(message)
    return logs
```

## Solution 07

```python
def only_even(numbers: list[int]) -> list[int]:
    return [number for number in numbers if number % 2 == 0]
```

This does not mutate the input list.

## Solution 08

```python
a = [1, 2]
b = [1, 2]

print(a == b)  # True: same value
print(a is b)  # False: different objects
```

## Solution 09

The default list is created once when the function is defined. All calls without an explicit `items` argument will reuse the same list.

Better:

```python
def create_order(items: list[str] | None = None) -> dict[str, list[str]]:
    return {"items": list(items) if items is not None else []}
```

## Solution 10

```python
def main() -> None:
    name = input("Name: ")
    print(f"Hello, {name}!")


if __name__ == "__main__":
    main()
```
