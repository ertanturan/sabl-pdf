# GitHub Releases auto-update plan

Status: Planned. The updater, distribution repository and release publishing workflow do not yet exist.

## Current state

SABL PDF is a Windows-only Python 3.12/PySide6 application. PyInstaller builds an onedir executable; Inno Setup 6 builds `dist/installer/SABL-PDF-Setup.exe`. The `.github/workflows/installer.yml` job currently uploads a CI artifact on `v*` tags, not an actual GitHub Release. Version `0.1.0` appears separately in `pyproject.toml`, `src/sabl_pdf/__init__.py` and `installer/SABL-PDF.iss`.

**Important distribution constraint:** the source repository, `ertanturan/sabl-pdf`, is private. Unauthenticated users cannot get release assets from a private GitHub repository. Keep source private and create a separate public binary-only repository, proposed name `ertanturan/sabl-pdf-releases`. Alternatively, the owner can make the source repository public before shipping. Never embed a GitHub access token or private-repository credential in the installed application.

## Desired experience

- Automatically check for a newer stable release on launch, without blocking document opening, and no more than once every 24 hours thereafter.
- Provide `Help > Check for updates` for an immediate manual check, `Help > What's new` for the installed version, and a setting to disable automatic checks.
- When an upgrade exists, show `Current vX.Y.Z`, `Available vA.B.C`, and only the four changelog sections for the new release, with `Update now`, `Later` and `Skip this version`.
- One click starts download, verification and setup. Show progress, allow cancel before installer launch, preserve PDF documents and app settings, and reopen SABL after a successful install.
- Show a clear error and manual release link when a check or update fails. Never block offline use or silently install or downgrade.

The app currently promises offline-first use: disclose that checking updates contacts GitHub over HTTPS, does not upload PDFs and can be disabled. No account, analytics, background PDF upload or privileged service is needed.

## System design

```text
Private source repo: tagged tested commit + frozen release notes
  -> Windows CI: test, package, sign, verify, upload
  -> Public release repo: GitHub Release vX.Y.Z
       - SABL-PDF-Setup-vX.Y.Z-x64.exe
       - update-manifest.json
       - update-manifest.json.sig
       - release notes for vX.Y.Z only

Installed SABL: Qt update checker
  -> public GitHub Releases API
  -> compare signed SemVer manifest against installed version
  -> show version-specific notes
  -> download + verify in user-owned staging folder
  -> save/close documents and launch installer
  -> updater process exits; Inno replaces app; reopen installed SABL
```

### Release publication

1. Use the changelog rules in `docs/plans/versioned-changelog.md`. Build only from an approved version tag pointing to tested `master`; require that `pyproject.toml` version, tag, release snapshot, Python executable version and Inno `AppVersion` agree.
2. Extend the existing Windows installer workflow to build, test and smoke-test the tagged release, bundle OCR data, then produce a **versioned** installer filename. Preserve the existing stable Inno `AppId` and installation scope to upgrade in place.
3. Generate the manifest containing schema version, release SemVer, Windows x64 platform, installer asset name, size, SHA-256, minimum supported app version where applicable and release tag. Sign the manifest using a dedicated release signing key stored outside the source repository (protected CI secrets or an approved signing service). Embed only the trusted public verification key in SABL.
4. Publish a draft public release with those assets and the frozen file `docs/changelog/releases/vX.Y.Z.md` as its **entire** body. Enable immutable releases in the public repository; publish only after every asset is attached and verified. Configure the stable release as the latest release. Do not publish a public source archive or sensitive build logs.
5. A publish job needs short-lived, narrowly scoped authorization to the public distribution repository (prefer a GitHub App installation token). Release failures must never produce a partial public stable release. Keep the private source and public distribution tags traceable to the same commit and checksum.
6. Source repository workflows must still support local `build.cmd` and installer creation without publishing. Local `build.cmd` increments the last version component by default, with `-Secondary`, `-Major`, `-Minor` and `-NoVersionBump` options. Tagged CI builds always pass `-NoVersionBump` and validate that `vX.Y.Z` equals the application version. Existing CI artifacts are not a substitute for release assets.

### Update checker

- Implement a pure update-domain service under `src/sabl_pdf/services/` for SemVer comparison, manifest validation, platform compatibility and upgrade decisions; inject a network/clock interface so tests run offline.
- Use nonblocking Qt networking in the UI coordinator. Query the **public** repository's `/repos/ertanturan/sabl-pdf-releases/releases/latest` endpoint; handle 404/no releases, limits, TLS, timeouts and malformed responses. Prefer ETag conditional requests and a 24-hour cache. Skip drafts and prereleases.
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
- A new version shows once, with only its own changelog, and can be installed by a single user action.
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

This plan does not create the distribution repository, publish a release, or change the shipped application.
