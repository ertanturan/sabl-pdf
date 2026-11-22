# SABL PDF Agent Instructions

## Product
- Windows-only desktop application built with Python 3.12+, PySide6 and PyMuPDF.
- Offline-first, no login, subscriptions, advertisements, telemetry or online services.
- One-purpose workflows and a simple, accessible interface.
- An installer registers the app as a PDF handler. Windows controls the user's default PDF app selection; never bypass the default-app consent mechanism.

## Architecture
- Organise production code as a `src/sabl_pdf` Python package.
- Keep PDF operations in small, independently testable service classes; the PySide6 UI only coordinates them.
- Each method performs one narrowly defined unit of work. Extract distinct operations into named helpers or collaborators.
- Use object-oriented design; follow SOLID principles, especially single responsibility and dependency inversion.
- Inject dependencies where appropriate. Keep pure business logic independent of widgets.
- Use descriptive public API names, explicit exceptions and typing.

## Editable placed content
- Every placed PDF item must be selectable by clicking it, repositionable with a held left mouse button, and removable with Delete or the item context menu.
- New placement tools must use the shared placed-item service and canvas interaction model.
- Every movable item, including future types, must be transferable between PDF pages through drag and drop.
- A cross-page move must preserve editable content, visual appearance, and save/reopen persistence; it must not flatten annotations.
- Drag previews must follow the destination page, support edge scrolling, and reject out-of-page drops.
- Add selection, same-page drag, cross-page drag, deletion, and persistence regression tests when adding new item types.
- Every placement tool must show a cursor-following preview before commit; make its size and landing position match the saved PDF item.
- Right-click and Escape must cancel an uncommitted placement without changing the document.

## Testing
- Implement unit tests for each feature or bugfix in the same PR.
- Follow Arrange, Act, Assert (AAA): separate setup, operation and verification clearly in every test.
- Cover successful operations, invalid inputs and state changes.
- Run `python -m pytest`, `python -m compileall -q src`, `ruff check .` and `python -m pyright` before opening PRs.
- Keep tests deterministic, offline and temporary-file based.

## Branches and commits
- Use stacked pull requests: each feature branch starts from its predecessor; each PR targets the preceding branch. First PR targets `master`.
- One logical work package per commit. If a proposed commit message needs the word "and", split the commit into smaller commits.
- Use small, imperative commits such as `feat: render PDF page` or `test: cover PDF zoom`.
- Keep refactors separate from feature commits. Do not mix unrelated bug fixes.
- Always create a pull request for every completed feature, bugfix, chore, refactor, docs, tests, build, or CI change without waiting for separate approval.
- Never merge pull requests. The repository owner merges manually after required CI checks pass.

## Pull request descriptions
- Create or update the corresponding pull request as part of every code or documentation change, without requesting separate approval.
- Use four headings: `Change type`, `What changed`, `How to test`, and `Stack`.
- Write short bullet points under every heading. Avoid paragraphs and broad claims.
- Label each change as feature, bugfix, tests, docs, refactor, build, or CI. Include every applicable type.
- Describe changes relative to the immediate parent branch, not `master`.
- Provide exact test commands and manual steps relevant to the changes.
- State whether each test was run, passed, failed, skipped, or not run. Never claim a test passed without evidence.
- Include the head branch, base branch, and previous PR dependency in the Stack section.
- Update the PR description when its scope or test results change.
- Keep PR titles short and scoped to one purpose.

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
- Changes reach master through pull requests only, after the `unit-tests` status check passes.
- The repository owner may merge their own PRs manually. No approving review is required.
- Root `manifest.json` describes the GitHub ruleset, but the active ruleset must be updated separately through GitHub settings.
- CODEOWNERS identifies maintainers without requiring an approval.
- Stacked dependencies must be respected before cleanup deletes a merged branch.
