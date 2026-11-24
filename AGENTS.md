# Simple PDF Agent Instructions

## Product
- All user-facing app, dialog, CLI, installer, release and Windows integration names use `Simple PDF`. Keep stable internal package, settings and PDF ProgID identifiers for compatibility.
- Windows-only desktop application built with Python 3.12+, PySide6 and PyMuPDF.
- Offline-first, no login, subscriptions, advertisements, telemetry or online services.
- One-purpose workflows and a simple, accessible interface.
- An installer registers the app as a PDF handler. Windows controls the user's default PDF app selection; never bypass the default-app consent mechanism.

## README hygiene
- Keep `README.md` accurate to features shipped on the target branch. Do not present backlog items or open PRs as available functionality.
- Update it in the same PR when user-visible features, requirements, commands, installation steps or known limitations change.
- Explain how to run, test and build the app with verified paths, prerequisites and expected outputs. Document material limitations and safety caveats.
- Use plain, precise language. Avoid filler, duplicate detail, unsupported claims, decorative sections and stale screenshots. Prefer links to dedicated documentation for deeper topics.
- Keep it concise without omitting information someone needs to use, troubleshoot or contribute to the project.

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
- Before making or reviewing **any code change** (feature, bugfix, refactor, test, build script, or CI code), read and apply `.agents/skills/unit-tests/SKILL.md`. Keep its requirements in scope throughout the change, even when no test file is touched.
- Follow Arrange, Act, Assert (AAA): separate setup, operation and verification clearly in every test.
- Keep unit tests and test fixtures free of logic: no branching, loops, comprehensions, or reimplementations of production behavior. Use fixed AAA steps and direct assertions.
- Cover successful operations, invalid inputs and state changes.
- Keep total line coverage for `sabl_pdf` at **80% or higher**. Every code-changing PR must run the full coverage gate and report the measured percentage; do not merge if it fails.
- Add or update AAA tests for changed behavior. Do not weaken assertions, exclude production files, or lower the coverage threshold to make checks pass.
- Treat a genuinely failing test as evidence of a defect: fix the production behavior, not the test. Never delete, skip, xfail, mock away, or relax a failing assertion merely to get a green CI result.
- Change an existing test only after demonstrating its expectation is wrong or obsolete, preserve the intended behavior with equivalent or stronger checks, and explain the evidence in the PR. If the defect cannot be fixed in scope, report the failure and leave CI red; push back on requests to hide it.
- Run `python -m pytest`, `python -m compileall -q src`, `ruff check .` and `python -m pyright` before opening code-changing PRs.
- CI skips Python tests, coverage and static checks only when every changed file has a documentation extension (`.md`, `.markdown`, `.mdown`, `.txt`, `.rst`, `.adoc`, `.asciidoc`). Keep the required `unit-tests` job successful through a lightweight documentation-only path. Mixed or unclassifiable changes must run the full checks.
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

## Pull request verification
- After each push, rebase, or changed PR base, wait for CI on the latest head SHA to finish. Use `gh pr checks <number> --watch` or the Actions run page; never rely on checks from a previous commit.
- Check that each PR is free of merge conflicts with its immediate base. Resolve real conflicts before rerunning test jobs; never overwrite or discard another change merely to force a clean merge.
- Investigate every failed, cancelled, or unexpectedly skipped required check. Read its GitHub Actions job and step logs with `gh run view <run-id> --log-failed`; reproduce the cause, implement the fix, push and recheck.
- Do not mark a PR ready while `merge-check` or the required `unit-tests` job is pending, skipped, failing, or older than its current head. The full coverage and static checks remain mandatory for code changes; a successful documentation-only `unit-tests` job may omit the Python steps.
- Verify stacked PRs parent-first, then check each child again after its parent is rebased or merged. Never auto-merge.
- If conflicts or CI failures cannot be fixed, record the exact failing check and blocker in the PR; leave the PR unmerged instead of bypassing the gate.

## Change logs
- Keep every release changelog bullet to 100 characters maximum, including its `- ` prefix. Split long details into separate bullets without omitting material facts.
- Update `docs/changelog/current.md` in the same PR as each release-worthy feature, fix or documentation change. Keep `- None.` only for empty sections; never bypass the release-notes guard.
- Record EVERY feature and bug fix in `docs/changes/YYYY-MM-DD.md` using the date of the change.
- Each entry includes change, branch, commit scope and corresponding test coverage.
- Append entries; never overwrite earlier records from the same date.
- Documentation-only or infrastructure commits may also be recorded for traceability.
- Follow `docs/plans/versioned-changelog.md` for the planned four-section release changelog.
- Only the current, unreleased version's changelog can be edited. NEVER edit, delete, rename, reorder, reclassify, or rewrite entries for any prior published version. This applies to all agents and contributors, including corrections.
- Record corrections to old changelogs as explicit new entries in the current version; never rewrite history.
- Never hand-edit generated cumulative history. Release automation and CI must verify every previous version's byte-for-byte integrity against its published commit.
- All GitHub Releases must contain only the matching version's new features, bugfixes, performance improvements, and documentation changes. Enable immutable GitHub Releases to protect published notes, tags, and assets.

## Build versioning
- Only the manually triggered `Publish Windows installer` GitHub Actions workflow increases a version automatically. It defaults to the last (`z`) component of `x.y.z`; selecting `secondary` increases `y` and resets `z`, while `major` increases `x` and resets `y.z`. Ordinary CI checks and local builds preserve the existing version. Explicit local `-Minor`, `-Secondary` and `-Major` remain available for deliberate development builds.
- Bumping must synchronise project metadata, Python application version and installer version before testing and packaging. Treat `pyproject.toml` as authoritative.
- The manual release action must bump once, freeze only the current release's four changelog sections, run Windows tests and installer smoke checks, then publish its versioned binary to the public source repository's GitHub Releases page using the workflow's built-in `GITHUB_TOKEN`. The packaging step MUST use `-NoVersionBump`; the build itself must not change the prepared release version. The source tag and generated release-record PR must match the installer. Never auto-merge the record PR.
- Never modify any published changelog as a side effect of version bumps. Only the current unreleased draft is writable when the changelog implementation is added.

## Release notes in the UI
- Help > What's New must always open the installed version's bundled release notes, including offline and without an open PDF.
- Closing release notes never disables future access; do not add a permanent dismissal option.
- Show release notes once after an installed-version change. Keep the Help action available on every launch.
- Keep release notes tied to the installed version, not the current unreleased draft or newest online release.

## Updates
- On application startup, check public GitHub Releases asynchronously, at most once per 24 hours after successful checks.
- Show a persistent, clickable update indicator for a newer stable version, including offline from a safe cache.
- Help > Check for Updates must bypass the cache and remain available when automatic checks are disabled.
- Provide an automatic-check setting. Never suppress Help > What's New or permit unchecked update installers to run.
- Never upload documents, collect analytics, or block PDF editing because a network check fails.

## Distribution
- Ship a Windows installer using PyInstaller with Inno Setup.
- Register a stable PDF ProgID with Windows. Offer PDF association; respect the user-controlled default application setting.
- Never collect analytics or send user files off-device.

## Main branch protection
- Changes reach master through pull requests only, after both `merge-check` and `unit-tests` status checks pass.
- The repository owner may merge their own PRs manually. No approving review is required.
- Root `manifest.json` describes the GitHub ruleset, but the active ruleset must be updated separately through GitHub settings.
- CODEOWNERS identifies maintainers without requiring an approval.
- Stacked dependencies must be respected before cleanup deletes a merged branch.
