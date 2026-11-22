## Change type
- Type: feature | bugfix | tests | docs | refactor | build | CI

## What changed
- Describe the first concrete change.
- Describe another change only when necessary.

## How to test
- Automated: `python -m pytest -q tests/test_feature.py` (not run).
- Manual: Describe the action and expected result, if applicable.
- Validation: `python -m ruff check .` (not run).
- Coverage for code changes: `python -m pytest -q --cov=sabl_pdf --cov-report=term-missing --cov-fail-under=80` (not run; report total percentage).

## Stack
- Head: `branch-name`
- Base: `parent-branch`
- Depends on: PR #N, or none.
