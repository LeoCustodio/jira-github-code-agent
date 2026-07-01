# Chapter 03 — Values, Objects, Names, and References

## Learning objectives

By the end of this chapter, you will be able to:

- Explain the difference between names and objects.
- Understand assignment in Python.
- Use `id`, `type`, equality, and identity correctly.
- Explain mutability and immutability.
- Avoid common bugs caused by shared mutable objects.

## Why this matters

Many Python bugs come from an incorrect mental model.

Beginners often imagine variables as boxes that contain values. In Python, that model is incomplete.

A better model is:

> A name is bound to an object.

Assignment does not copy an object by default. Assignment creates or changes a binding between a name and an object.

## Objects

Every object has:

1. identity,
2. type,
3. value.

Example:

```python
x = 42

print(id(x))
print(type(x))
print(x)
```

`id(x)` returns an identity value for the object during its lifetime. In CPython, this is often related to the memory address, but code should not depend on that implementation detail.

## Names

A name is a label that points to an object.

```python
a = [1, 2, 3]
b = a

b.append(4)

print(a)
print(b)
print(a is b)
```

Expected output:

```text
[1, 2, 3, 4]
[1, 2, 3, 4]
True
```

`a` and `b` refer to the same list object. Appending through `b` changes the object that `a` also references.

## Equality vs identity

Equality asks whether two objects have equal values.

Identity asks whether two names reference the exact same object.

```python
a = [1, 2, 3]
b = [1, 2, 3]

print(a == b)
print(a is b)
```

Expected output:

```text
True
False
```

Use `==` for value comparison. Use `is` for identity checks, especially `None`:

```python
if user is None:
    print("No user")
```

Do not write:

```python
if user == None:
    ...
```

## Mutability

Mutable objects can be changed after creation.

Examples:

- list
- dict
- set
- most custom objects

Immutable objects cannot be changed after creation.

Examples:

- int
- float
- bool
- str
- tuple
- frozenset

Important nuance: a tuple is immutable, but it can contain mutable objects.

```python
t = ([1, 2], [3, 4])
t[0].append(99)
print(t)
```

The tuple still points to the same list objects, but the list object was mutated.

## Assignment does not copy

```python
original = {"roles": ["admin"]}
copy = original

copy["roles"].append("owner")

print(original)
```

Expected output:

```text
{'roles': ['admin', 'owner']}
```

Both names point to the same dictionary.

## Shallow copy vs deep copy

A shallow copy creates a new outer object, but nested objects are shared.

```python
original = {"roles": ["admin"]}
shallow = original.copy()

shallow["roles"].append("owner")

print(original)
print(shallow)
```

Both dictionaries contain the changed nested list.

A deep copy recursively copies nested objects:

```python
from copy import deepcopy

original = {"roles": ["admin"]}
clone = deepcopy(original)

clone["roles"].append("owner")

print(original)
print(clone)
```

## Function arguments

Python passes object references by assignment.

```python
def add_item(items: list[str]) -> None:
    items.append("new")


values = ["old"]
add_item(values)
print(values)
```

Expected output:

```text
['old', 'new']
```

The function receives a name bound to the same list object.

## Dangerous default arguments

This is one of the classic Python bugs:

```python
def add_task(task: str, tasks: list[str] = []) -> list[str]:
    tasks.append(task)
    return tasks


print(add_task("A"))
print(add_task("B"))
```

Expected output:

```text
['A']
['A', 'B']
```

The default list is created once when the function is defined, not each time it is called.

Correct version:

```python
def add_task(task: str, tasks: list[str] | None = None) -> list[str]:
    if tasks is None:
        tasks = []
    tasks.append(task)
    return tasks
```

## Production example

Imagine a request handler that modifies a default permissions list.

Bad:

```python
def create_user(name: str, permissions: list[str] = ["read"]) -> dict[str, object]:
    permissions.append("profile")
    return {"name": name, "permissions": permissions}
```

This leaks permissions across users.

Better:

```python
def create_user(name: str, permissions: list[str] | None = None) -> dict[str, object]:
    effective_permissions = list(permissions) if permissions is not None else ["read"]
    effective_permissions.append("profile")
    return {"name": name, "permissions": effective_permissions}
```

## CPython/runtime details

CPython manages objects with reference counting plus a cyclic garbage collector.

When a name is bound to an object, the object's reference count increases. When a name is rebound or goes out of scope, the reference count decreases.

Example:

```python
import sys

items = []
print(sys.getrefcount(items))
```

`getrefcount` itself temporarily creates an additional reference, so the number may be higher than expected.

## Best practices

- Use `is None` for None checks.
- Be cautious when passing mutable objects to functions.
- Avoid mutable default arguments.
- Copy intentionally and document whether a function mutates input.
- Prefer immutable data when sharing across boundaries.

## Anti-patterns

- Using `is` to compare strings or numbers.
- Mutating input unexpectedly.
- Returning internal mutable state directly.
- Assuming assignment copies data.
- Using mutable default arguments.

## Exercises

### Exercise 1

Predict the output:

```python
a = [1, 2]
b = a
c = a.copy()

b.append(3)
c.append(4)

print(a)
print(b)
print(c)
```

### Exercise 2

Fix this function:

```python
def register_event(event: str, events: list[str] = []) -> list[str]:
    events.append(event)
    return events
```

### Exercise 3

Write a function that receives a list and returns a new list without mutating the original.

## Solutions

### Solution 1

```text
[1, 2, 3]
[1, 2, 3]
[1, 2, 4]
```

`a` and `b` reference the same object. `c` is a shallow copy.

### Solution 2

```python
def register_event(event: str, events: list[str] | None = None) -> list[str]:
    if events is None:
        events = []
    events.append(event)
    return events
```

### Solution 3

```python
def without_negatives(numbers: list[int]) -> list[int]:
    return [number for number in numbers if number >= 0]
```

## Quiz

1. What is the difference between equality and identity?
2. Why are mutable default arguments dangerous?
3. Does assignment copy an object?
4. What is a shallow copy?
5. Why can a tuple contain mutable objects?

## Interview questions

1. Explain Python's assignment model.
2. What happens when a mutable object is passed to a function?
3. How do you avoid shared mutable state bugs?
4. What does CPython reference counting do?

## Summary

Python names are bindings to objects. Assignment binds names; it does not copy objects. Understanding identity, equality, mutability, and references is essential before learning collections, functions, OOP, concurrency, and architecture.
