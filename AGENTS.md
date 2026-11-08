# SABL PDF Agent Instructions

## Product
- Windows-only desktop application built with Python 3.12+, PySide6 and PyMuPDF.
- Offline-first, no login, subscriptions, advertisements, telemetry or online services.
- One-purpose workflows and a simple, accessible interface.
- An installer registers the app as a PDF handler. Windows controls the user's default PDF app selection; never bypass the default-app consent mechanism.

## Architecture
- Organise production code as a `src/sabl_pdf` Python package.
- Keep PDF operations in small, independently testable service classes; the PySide6 UI only coordinates them.
- Use object-oriented design; follow SOLID principles, especially single responsibility and dependency inversion.
- Inject dependencies where appropriate. Keep pure business logic independent of widgets.
- Use descriptive public API names, explicit exceptions and typing.

## Testing
- Implement unit tests for each feature or bugfix in the same PR.
- Follow Arrange, Act, Assert (AAA): separate setup, operation and verification clearly in every test.
- Cover successful operations, invalid inputs and state changes.
- Run `python -m pytest`, `python -m compileall -q src` and `ruff check .` before opening PRs.
- Keep tests deterministic, offline and temporary-file based.

## Branches and commits
- Use stacked pull requests: each feature branch starts from its predecessor; each PR targets the preceding branch. First PR targets `master`.
- One logical work package per commit. If a proposed commit message needs the word "and", split the commit into smaller commits.
- Use small, imperative commits such as `feat: render PDF page` or `test: cover PDF zoom`.
- Keep refactors separate from feature commits. Do not mix unrelated bug fixes.
- Do not merge stacked PRs until earlier PRs are reviewed.

## Change logs
- Record EVERY feature and bug fix in `docs/changes/YYYY-MM-DD.md` using the date of the change.
- Each entry includes change, branch, commit scope and corresponding test coverage.
- Append entries; never overwrite earlier records from the same date.
- Documentation-only or infrastructure commits may also be recorded for traceability.

## Distribution
- Ship a Windows installer using PyInstaller with Inno Setup.
- Register a stable PDF ProgID with Windows. Offer PDF association; respect the user-controlled default application setting.
- Never collect analytics or send user files off-device.

## Main branch protection
- Changes reach master through reviewed PRs only, after the `unit-tests` status check passes.
- Root `manifest.json` describes the GitHub ruleset, but must be applied using repository admin permissions.
- CODEOWNERS requests @ertanturan's review; GitHub does not permit self-approval of a PR you authored.
- Stacked dependencies must be respected before cleanup deletes a merged branch.
