# GitHub Releases auto-update plan

Status: Manual GitHub Actions releases target the public `ertanturan/sabl-pdf` repository. Offline What's New and manual/automatic release detection are implemented in separate stacked PRs. Signed update manifests, verified one-click installation and installer relaunch remain planned.

## Current state

SABL PDF is a Windows-only Python 3.12/PySide6 application. PyInstaller builds an onedir executable; Inno Setup 6 builds `dist/installer/SABL-PDF-Setup-vX.Y.Z-x64.exe`. The `.github/workflows/installer.yml` job uses manual `workflow_dispatch` and an automatic selected version increment to build and stage/publish a versioned GitHub Release. Version `0.1.0` appears separately in `pyproject.toml`, `src/sabl_pdf/__init__.py` and `installer/SABL-PDF.iss`.

**Distribution:** `ertanturan/sabl-pdf` is public. Releases and installers belong in this same repository. No distribution-only repository or access token in the installed application is required.

## Desired experience

- Automatically check for a newer stable release on launch, without blocking document opening, and no more than once every 24 hours thereafter.
- Keep `Help > What's New` always available with offline notes for the installed version, including after updates. On launch after a recorded version change, show those notes once, without a permanent opt-out. Add `Help > Check for updates` for an immediate manual check and a setting to disable automatic checks.
- When an upgrade exists, show `Current vX.Y.Z`, `Available vA.B.C`, and only the four changelog sections for the new release, with `Update now` and `Later`. Do not offer a permanent changelog-dismissal option.
- One click starts download, verification and setup. Show progress, allow cancel before installer launch, preserve PDF documents and app settings, and reopen SABL after a successful install.
- Show a clear error and manual release link when a check or update fails. Never block offline use or silently install or downgrade.

The app currently promises offline-first use: disclose that checking updates contacts GitHub over HTTPS, does not upload PDFs and can be disabled. No account, analytics, background PDF upload or privileged service is needed.

## System design

```text
Public ertanturan/sabl-pdf: tagged source commit + frozen release notes
  -> Windows CI: test, build, smoke-test, checksum, publish
  -> GitHub Release vX.Y.Z in this repository
       - SABL-PDF-Setup-vX.Y.Z-x64.exe
       - SABL-PDF-Setup-vX.Y.Z-x64.exe.sha256
       - release notes for vX.Y.Z only

Future one-click update delivery adds signed update-manifest.json(.sig)
to the same release; signatures are not implemented yet.

Installed SABL: Qt update checker
  -> public GitHub Releases API
  -> compare signed SemVer manifest against installed version
  -> show version-specific notes
  -> download + verify in user-owned staging folder
  -> save/close documents and launch installer
  -> updater process exits; Inno replaces app; reopen installed SABL
```

### Release publication

1. Use the changelog rules in `docs/plans/versioned-changelog.md`. A manually triggered workflow on `master` selects the next version (`minor` by default, or `secondary`/`major`), freezes that version's changelog, creates a versioned source commit and tag, and builds from that exact source state. The release-record PR must be merged manually before triggering another release. Require the project, tag, snapshot, application and installer versions to agree.
2. Extend the existing Windows installer workflow to build, test and smoke-test the tagged release, bundle OCR data, then produce a **versioned** installer filename. Preserve the existing stable Inno `AppId` and installation scope to upgrade in place.
3. **Future updater prerequisite:** generate a signed update manifest containing release SemVer, platform, installer name, size, SHA-256, supported versions, and tag. Store the signing private key in protected CI secrets or a signing service and embed only its public key in SABL. The current manual release workflow publishes an installer and SHA-256 checksum, not a signed manifest.
4. Publish a draft release in `ertanturan/sabl-pdf` using `docs/changelog/releases/vX.Y.Z.md` as its **entire** body. Enable immutable releases in this repository; publish after assets are attached and verified, and mark stable releases as latest. GitHub supplies source archives for releases of this public repository.
5. Use the workflow's built-in `GITHUB_TOKEN` with `contents: write`, `pull-requests: write`, and `actions: write`. Configure repository Actions permissions to permit branch pushes, pull request creation, and explicit CI dispatch for the release-record branch. Publish only after a versioned source tag exists in the same repository. Failed runs must leave any incomplete release as a draft rather than a partial public stable release.
6. Ordinary CI and local `build.cmd` builds must never auto-increment versions or publish GitHub Releases. Only the manual GitHub Actions release workflow may bump versions automatically and distribute the binary. Explicit local version bump flags remain available for development. The installer packaging step always passes `-NoVersionBump` to preserve the version prepared for that release. Existing CI artifacts are not substitutes for public release assets.

### Update checker

- Implement a pure update-domain service under `src/sabl_pdf/services/` for SemVer comparison, manifest validation, platform compatibility and upgrade decisions; inject a network/clock interface so tests run offline.
- Use nonblocking Qt networking in the UI coordinator. Query `/repos/ertanturan/sabl-pdf/releases/latest`; handle 404/no releases, limits, TLS, timeouts, and malformed responses. Prefer ETag conditional requests and a 24-hour cache. Skip drafts and prereleases.
- Reject versions less than or equal to the installed version, non-`vMAJOR.MINOR.PATCH` tags, unknown architectures, or missing manifest/installer assets. Do not infer a download URL from an arbitrary release description.
- Use release-specific GitHub body text for the update dialog, never the cumulative `CHANGELOG.md`. Validate/limit displayed Markdown and never execute links or scripts from it.
- Keep a single update check/download active, support user cancellation, and remember a skipped version. Manual checks bypass the 24-hour automatic-check limit.

### Safe one-click installer handoff

- Download to a per-user staging folder outside the app installation directory and write via a temporary filename until complete. Check disk space, transfer length, SHA-256 and the signature of the manifest using an embedded public key before executing any downloaded bytes.
- GitHub HTTPS and a hash published beside the binary alone are **not** a publisher authenticity guarantee. Do not allow one-click execution without the pinned signature verification step. Prefer Authenticode-signed installers too, to reduce Windows trust warnings; do not bypass SmartScreen or UAC.
- Ask the current multi-tab window to save or explicitly discard unsaved edits. Cancel the update if any document cannot close safely or if the user cancels.
- Launch a verified Inno installer only after confirming it is an allowed upgrade. Use documented silent flags with `/NORESTART` and preserve the existing user installation directory; do not kill an app containing unsaved work. Use a small outside-the-install-directory handoff helper only if process shutdown or restart coordination requires it.
- Exit SABL cleanly, update the installed files, then relaunch on successful completion. Display a failure and a link to manual installation if setup does not succeed. Do not promise atomic rollback: Inno Setup is not a transactional package manager.
- Preserve user settings and existing PDF files. Clean staging data only after safe completion or on the next run. A power loss or interrupted download must not launch an incomplete installer.

## Proposed implementation sequence

1. **Release foundation PR:** shared version derivation, tagged release validation, frozen changelog gating and GitHub release publishing (depends on the changelog plan).
2. **Update detection PR:** pure version/manifest service, offline tests and PySide6 update notification, manual checking and privacy settings.
3. **Verified delivery PR:** signed-manifest verification, download state/progress, cancellation and retry, tests for bad signatures and corrupt assets.
4. **Install and resume PR:** safe unsaved-document handling, installer handoff, close/relaunch and tests for interrupted installs.
5. **Windows release smoke PR:** test upgrading an installed old version to a new one, preserving app data, uninstaller metadata and file association.

Do not enable one-click installation until signature and recovery tests pass. Each stage is a separate, small PR following existing branch, AAA testing and coverage requirements.

## Acceptance

- A publicly installed SABL can check for a stable release without private-repository access or credentials.
- After an upgrade, show that version's notes and keep them accessible through Help > What's New at any time, without a permanent dismissal option. Installation may require a single user action once safely verified.
- No newer release, network offline, 404, rate limits and malformed metadata leave the app responsive and usable.
- Missing/wrong signing key, altered manifest, SHA mismatch, wrong platform and downgrade never execute the installer.
- Unsaved PDFs are saved with consent or keep the current app open; there is no silent document loss.
- Upgrading preserves the stable Inno `AppId`, settings, user documents, optional PDF association and uninstallability.
- The app works normally if update checks are disabled. No PDF contents or analytics are sent to GitHub.
- Automated tests use AAA without control-flow statements in test bodies; changed production code keeps at least 80% coverage. Windows smoke tests exercise true installer upgrade and restart.

## Dependencies and references

- [Versioned changelog plan](versioned-changelog.md)
- [Current installer workflow](../../.github/workflows/installer.yml)
- [Inno Setup command-line parameters](https://jrsoftware.org/inno-setup/documentation/topic_setupcmdline.htm)
- [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
- [GitHub releases API](https://docs.github.com/en/rest/releases/releases)

The release workflow is manually triggered and publishes installers in the existing public source repository. This plan does not implement or enable the in-app updater.
