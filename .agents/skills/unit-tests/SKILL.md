---
name: unit-tests
description: Write, change, and review SABL PDF pytest unit tests using Arrange, Act, Assert (AAA). Use this skill for every unit test, regression test, and test fixture change.
---

# Unit tests

Use the Arrange, Act, Assert (AAA) pattern for every test in `tests/`.

## Structure

1. **Arrange:** Prepare fixtures, inputs, expected values, and the object under test. Prefer shared `pytest` fixtures when setup is reused.
2. **Act:** Perform one behavior under test. Keep the operation distinct from setup and verification.
3. **Assert:** Check the observable result and relevant state changes with specific assertions. Related assertions can verify the same behavior.

Separate the phases with blank lines. Descriptive names and spacing should make the phases evident without comments.

For expected failures, `pytest.raises` is the assertion that encloses the Act phase. Add `match=` when the exception message is part of a stable contract.

## Example

```python
from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.pages import PageService


def test_rotate_page(session: DocumentSession) -> None:
    service = PageService(session)

    service.rotate(0)

    assert session.document[0].rotation == 90
```

```python
import pytest

from sabl_pdf.core.session import DocumentSession
from sabl_pdf.services.pages import PageService


def test_delete_only_page_is_rejected(session: DocumentSession) -> None:
    service = PageService(session)

    with pytest.raises(ValueError):
        service.delete(0)
```

## No logic in tests

Unit tests must be straight-line Arrange, Act, Assert code. A test documents behavior; it must not implement, re-create, or decide that behavior.

- Never write `if`, `elif`, `else`, `for`, `while`, `match`, or other branching or iteration in unit tests, test-only helpers, or fixtures.
- Do not use conditional expressions, comprehensions, `any()`, `all()`, `map()`, `filter()`, or loops disguised as expressions.
- Do not calculate expected results, transform actual results, implement algorithms, or duplicate production logic inside tests.
- Arrange fixed inputs and literal expected values, Act by calling the unit under test, then Assert the observable output or state directly.
- Use separate named tests or `@pytest.mark.parametrize` with static cases for different inputs and outcomes. Never branch on a scenario inside a test.
- Keep fixtures limited to straightforward data and resource setup/teardown. Move behavior to production code rather than creating test-only implementations of it.
- `with pytest.raises(...)` is permitted to assert an exception; it is not application logic.

## Rules

- Use one behavior per test; separate unrelated operations or outcomes into separate tests.
- Name tests for the scenario and expected behavior, not the implementation.
- Cover happy paths, boundaries, invalid inputs, and state changes relevant to the change.
- For a bug fix, reproduce the failure in a regression test before fixing the production code.
- Keep tests deterministic, offline, independent, and free of shared mutable state.
- Use `tmp_path`, `monkeypatch`, and fixtures instead of persistent files, external services, and timing assumptions.
- Assert externally observable behavior rather than private implementation details.
- Put reusable setup and cleanup in fixtures; do not hide the Act or Assert phases in helpers.

## Validation

Run the focused test first, then the project checks before opening a PR:

```powershell
python -m pytest -q tests/test_<feature>.py
python -m pytest
python -m compileall -q src
ruff check .
```

Report which commands actually ran and their results in the PR. Include additional required checks configured by the branch's CI.
