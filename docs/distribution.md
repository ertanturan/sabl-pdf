# Simple PDF distribution and discoverability

Use [the repository](https://github.com/ertanturan/sabl-pdf) as the public product URL. No standalone website is required.

## Reusable listing details

- **Name:** Simple PDF
- **Short description:** Free, offline PDF editor for Windows. Annotate, sign, fill forms, redact information and organise PDF pages locally.
- **Project URL:** https://github.com/ertanturan/sabl-pdf
- **Download URL:** https://github.com/ertanturan/sabl-pdf/releases/latest
- **Platform:** Windows x64
- **Price:** Free; no account or subscription
- **Privacy:** Documents are processed locally. The optional update check contacts GitHub Releases; it never uploads documents.
- **Categories:** PDF editor, PDF viewer, document annotation, PDF utilities
- **Tags:** pdf-editor, pdf-viewer, windows, offline, pdf-annotation, pdf-redaction, privacy, pyside6, pdf-tools
- **Licence:** Not yet specified in a root `LICENSE` file. The public source repository alone does not grant open-source reuse rights. Choose and publish a licence before describing the project as open source on software directories.

**Long description:** Simple PDF is a free Windows desktop app for opening and working with PDF files offline. Fill forms, add movable text boxes, annotate pages, place drawn or image signatures, redact sensitive content, compress documents and merge, split, rotate or reorder pages. It does not require an account or upload documents to an online service.

**State limitations honestly:** Existing page text cannot be edited in place; visual signatures are not certificate-based digital signatures. OCR extracts text but does not yet insert a searchable text layer into scanned PDFs. Redacted copies are flattened to images. See [README limitations](../README.md#important-limitations).

## GitHub About metadata (one-time manual update)

Open the [repository](https://github.com/ertanturan/sabl-pdf), select the gear icon beside **About**, and set:

- **Description:** Free, offline PDF editor for Windows. Sign, annotate, redact and organise PDFs without subscriptions.
- **Website:** https://github.com/ertanturan/sabl-pdf
- **Topics:** `pdf-editor`, `pdf-viewer`, `windows`, `offline`, `privacy`, `pdf-tools`, `pdf-annotation`, `pdf-redaction`, `pyside6`, `desktop-app`

Add the `open-source` topic only after publishing an appropriate software licence.

Capture and upload genuine application screenshots showing the viewer and at least one editing workflow. Use a screenshot from a released build, with fictitious document content, rather than a mockup. A social preview image can be uploaded separately through GitHub repository settings. Do not publish screenshots of personal documents.

## WinGet submission

1. Publish and smoke-test a versioned Windows installer on [GitHub Releases](https://github.com/ertanturan/sabl-pdf/releases), including its SHA-256 checksum. Use an immutable, version-specific installer URL in the WinGet manifest.
2. On Windows, install the [Windows Package Manager Manifest Creator](https://github.com/microsoft/winget-create): `winget install Microsoft.WingetCreate`.
3. Run `wingetcreate new "<version-specific installer URL>"` and provide the publisher, package identifier, version, installer type (Inno Setup), licence and other requested fields.
4. Validate and test the resulting manifest and silent installer behaviour. Submit a PR to [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs); follow its contributor agreement and validation feedback.
5. After acceptance, record the exact approved package identifier in the README. Use [wingetcreate update](https://github.com/microsoft/winget-create/blob/main/doc/update.md) for later versions.

Follow [Microsoft's manifest guidance](https://learn.microsoft.com/en-us/windows/package-manager/package/manifest). Do not advertise a `winget install` command until the package is accepted.

### Automatically submit updates after releases

The `.github/workflows/update-winget.yml` workflow runs after a successful **Publish Windows installer** workflow, or can be started manually from **Actions > Update WinGet package** with an optional published release tag.

Enable this only **after the first `SABL.SimplePDF` package has been approved and merged** in `microsoft/winget-pkgs`:

1. Create a [GitHub classic personal access token](https://github.com/settings/tokens) with `public_repo` scope. WingetCreate does not support fine-grained tokens for this operation.
2. Under **Settings > Secrets and variables > Actions > Secrets**, add a repository secret named `WINGET_PAT` containing that token.
3. Under **Settings > Secrets and variables > Actions > Variables**, set the repository variable `WINGET_ENABLED` to `true`.
4. Publish a version normally. The workflow resolves the new stable GitHub Release, verifies the expected x64 installer asset and asks WingetCreate to submit an updated manifest PR.
5. Track the resulting PR at [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs/pulls). Microsoft still controls acceptance; do not assume the version is immediately available.
6. If a submission fails, fix the cause and manually run **Update WinGet package** with the exact release tag. Set `WINGET_ENABLED` to `false` to pause submissions.

The token is passed through WingetCreate's documented `WINGET_CREATE_GITHUB_TOKEN` environment variable, never as a command-line argument. The default `GITHUB_TOKEN` cannot submit PRs to the Microsoft repository. Do not publish the token in logs or files.

## AlternativeTo submission

1. Register and verify an account on [AlternativeTo](https://alternativeto.net/).
2. Choose **Suggest new application** from the user menu.
3. Enter the listing details above, link to the repository, select Windows and the accurately declared licence, and attach genuine screenshots.
4. Submit for moderation. Once listed, add relevant alternatives only where the features genuinely overlap.
5. Optionally [request developer access](https://alternativeto.net/developers/) to maintain the listing.

See [AlternativeTo's official FAQ](https://alternativeto.net/faq/). Do not claim the application is open source until a software licence is published.

## Community launch

Share the released app, actual screenshots, download link and limitations with suitable communities such as Show HN, Indie Hackers, Product Hunt and open-source/software subreddits, following each community's rules. Avoid paid endorsements, fabricated reviews, repetitive posts and unsupported feature claims.

## Release checklist

- [ ] Select and publish an explicit software licence
- [ ] Set GitHub About description, repository URL and topics
- [ ] Capture real screenshots and upload a GitHub social preview
- [ ] Submit a WinGet manifest and confirm acceptance
- [ ] Submit an AlternativeTo listing and confirm acceptance
- [ ] Share a release with relevant communities
