# Versioned changelog plan

Status: The draft, frozen note snapshot, cumulative generator, integrity check and manually triggered release preparation are implemented in PR #55. Repository release settings and public distribution still require configuration.

## Goal

Keep honest release-by-release notes and a complete, readable history. A published version is permanent: neither humans nor agents may rewrite, remove, reorder, or reclassify its history. A correction belongs in the current unreleased version, pointing back to the original release.

## Files and ownership

- `docs/changelog/current.md`: only editable release-note draft, for the next planned version.
- `docs/changelog/releases/vX.Y.Z.md`: one frozen Markdown snapshot per published version.
- `CHANGELOG.md`: generated complete history containing the full text of every published version, newest first, plus a link to the current draft. Never hand-edit it.
- `docs/changes/YYYY-MM-DD.md`: preserve existing detailed development records; append new records per the existing agent rule. These logs can record tests and internal-only infrastructure changes that do not belong in user-facing notes.
- `scripts/changelog.py` (planned): validate, freeze, assemble and compare release notes without modifying an older version.

A release page receives exactly the contents of its own version file, not the whole `CHANGELOG.md`. Each release contains these four headings in this order, even when a section is empty:

```markdown
# v0.2.0 (YYYY-MM-DD)

## New features
- Description of the user-visible change. (#PR)

## Bugfixes
- Description of the corrected behaviour. (#PR)

## Performance improvements
- Description, preferably with measured evidence. (#PR)

## Documentation
- Description of the documentation update. (#PR)
```

Use `- None.` in an empty section. Entries must say what changed, not promise future work. No generated GitHub commit dump or cumulative notes on an individual release page.

## Working rules

1. During development, edit only `current.md`, assigning each relevant change to exactly one of the four categories and linking its PR. A commit touching multiple categories may have separate entries. Do not invent performance claims.
2. Keep one shared version source, `pyproject.toml`. Only manually triggering the GitHub Actions installer release workflow automatically increments `z` in `x.y.z` by default. Its `secondary` option increments `y` and resets `z`; `major` increments `x` and resets `y.z`. Ordinary CI and local builds preserve the version. The release job synchronises Python and Inno Setup versions before building with `-NoVersionBump`. Use SemVer tags `vMAJOR.MINOR.PATCH` (the user's names are major, secondary and minor).
3. When preparing a release, validate the current draft and version, freeze it as `releases/vX.Y.Z.md`, and regenerate `CHANGELOG.md` from all snapshots without changing any previous release's bytes. The manually triggered release action resets only the current editable draft after freezing. No ordinary build may rewrite previous release history.
4. Build and test the exact tagged commit; publish the matching release only after checks and a Windows installer smoke test pass. GitHub release notes come solely from `releases/vX.Y.Z.md`.
5. Once a version is published, lock its snapshot and release metadata. Never modify any earlier version entry in any PR, branch or agent task.
6. Advance the editable draft to the next intended version only after publishing the current one. Previous released versions remain frozen.
7. If an old description was inaccurate, write an explicit correction in the current version; do not silently rewrite the old entry. Keep audit links to the original PR and tag.

## Enforced historical integrity

- The changelog validator must read published release tags and the protected snapshot index, compare each historical file with the bytes recorded at its original release commit, and reject changes, deletions, renames and inserted entries for older versions.
- Regeneration of `CHANGELOG.md` must prove all prior version sections are identical. CI rejects a direct edit or a mismatch with generated output.
- Reject duplicate versions, reordered categories, malformed SemVer, a tag/version mismatch and a release without a matching snapshot.
- Require CI checks and PR merges to `master`; deny direct pushes and non-fast-forward changes under repository rules. No agent merges PRs.
- Enable GitHub's **immutable releases** repository setting before publishing. It protects future published release notes, assets and associated tags and supplies release attestations; it does not by itself protect ordinary repository files.
- These rules prevent accidental and normal unauthorized editing. A repository administrator who can change protection settings is outside the guarantee; audit such exceptions instead of claiming absolute immutability.

## First release and legacy records

The repository currently uses version `0.1.0` in three places and already has dated development notes. Check existing tags/releases before freezing the first version. Preserve `docs/changes/` as-is; do not invent earlier release notes or relabel an old development entry as a shipped release. The first release snapshot must reflect only work genuinely included in that published binary.

## Acceptance

- Every released version has exactly one frozen note file and a matching GitHub Release.
- GitHub shows only that release's four categories; `CHANGELOG.md` has the exhaustive history.
- A PR that edits, deletes or renames a previously released note fails CI, including with a generated-history refresh.
- A correction appended to the current version passes without touching historical bytes.
- Missing/duplicate sections, mismatched versions, no release asset and dirty generated history fail validation.
- Tests follow AAA with no branching/loops in test bodies; changed production code maintains at least 80% coverage.

## Planned implementation PRs

1. Add draft, snapshot, generator and changelog validator with focused tests.
2. Consolidate build-time versioning and enforce changelog checks in CI.
3. Connect release tagging and GitHub Release publishing to the frozen snapshot and enable immutable releases.

Implementation must land in separate reviewable PRs; this file is the design only.
