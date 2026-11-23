# Simple PDF

**A free, offline PDF editor for Windows.** Open and annotate PDFs, fill forms, sign documents, redact sensitive information, and merge, split or organise pages. Your documents stay on your computer: no account, subscription, advertising, telemetry or cloud upload.

**[Download the latest Windows installer](https://github.com/ertanturan/sabl-pdf/releases/latest)** | [All releases and checksums](https://github.com/ertanturan/sabl-pdf/releases) | [Source code](https://github.com/ertanturan/sabl-pdf)

The Windows x64 installer is named `Simple-PDF-Setup-vX.Y.Z-x64.exe`. Download it from GitHub Releases and run it to install Simple PDF. If you prefer to run from source, see [Run from source](#run-from-source-windows).

## See Simple PDF in action

Watch a short preview of the Windows app before downloading it.

https://github.com/user-attachments/assets/018b59c9-d6df-444e-9efa-a0dfa5ada268

## Features

- **Viewing:** Open PDFs in separate tabs, find and select text (including scanned text through local OCR), zoom, use page thumbnails and copy selections.
- **Text and forms:** Add, edit, move or remove text-box annotations; fill PDF text and checkbox fields.
- **Signatures:** Draw and reuse a signature, or place a PNG/JPEG signature image.
- **Pages:** Merge PDFs, split page ranges, delete, rotate or reorder pages.
- **Annotations:** Highlight, underline, add notes and remove annotations.
- **Redaction:** Redact selected text, page areas or searched phrases into a separate, checked PDF copy.
- **Compression:** Optimise PDF object streams and optionally recompress images. Savings depend on the file.
- **Conversion:** Add images as PDF pages or export PDF pages as PNG files.
- **OCR:** Recognise scanned-page text locally using Tesseract OCR and export it as text. Tesseract OCR support and language data must be available.
- **Release notes:** Read the installed version's changelog offline with **Help > What's New**. Notes also appear after upgrades and remain accessible.
- **Updates:** Check GitHub Releases on startup, at most once per 24 hours. Click the persistent update notice, then **Update now** to download a SHA-256 verified installer, install it and relaunch Simple PDF automatically. **View on GitHub** remains available. Use **Help > Check for Updates** anytime or disable automatic checks under Help. One-click installation requires the installed Windows app, not a source checkout.

## Tech Stack

- **Python 3.12+** for the application and PDF services.
- **PySide6 (Qt)** for the Windows desktop interface.
- **PyMuPDF** for PDF rendering, text extraction and document operations.
- **Pillow** for image handling; **Tesseract OCR** for scanned-page text recognition through PyMuPDF.
- **PyInstaller** for executable packaging and **Inno Setup 6** for the Windows installer.

## Run from source (Windows)

Requires **Python 3.12+** available as `py` or `python`. From a checkout, double-click `run.cmd`, or use the commands below in the repository root:

| Launcher | What it does |
| --- | --- |
| `run.cmd` | Creates/reuses `.venv`, installs project and development dependencies, and opens the app. |
| `test.cmd` | Prepares the environment, then runs pytest, Python compilation and Ruff. |
| `build.cmd` | Checks the existing version, runs tests, builds with PyInstaller and creates the Windows installer. |

Python package installations also provide the `simple-pdf` command; `sabl-pdf` remains an alias for compatibility.

The PowerShell equivalents are `./scripts/run.ps1`, `./scripts/test.ps1` and `./scripts/build.ps1`. The `.cmd` launchers are intended for double-clicking; they invoke PowerShell without requiring a permanent execution-policy change. Tests use Qt offscreen mode.

### Build version numbers

The manually triggered GitHub release workflow increments the version automatically. Simple PDF uses `x.y.z` with `x` as major, `y` as secondary and `z` as minor. Ordinary local and CI builds preserve their current version.

| Command | Example from `0.1.9` |
| --- | --- |
| GitHub Actions release: `minor` (default) | `0.1.10` |
| GitHub Actions release: `secondary` | `0.2.0` |
| GitHub Actions release: `major` | `1.0.0` |
| `build.cmd` (normal local build) | `0.1.9` |

### Publish a Windows installer

Releases are created in this public repository at [GitHub Releases](https://github.com/ertanturan/sabl-pdf/releases). The installer workflow runs **only when manually triggered**, not on normal pushes or merges.

1. In **Settings > Actions > General**, enable GitHub Actions workflow **Read and write permissions** and **Allow GitHub Actions to create and approve pull requests**. The release workflow uses the built-in `GITHUB_TOKEN`; no personal access token or second repository is needed.
2. Make sure branch and tag rules permit GitHub Actions to create `release/vX.Y.Z` branches and `vX.Y.Z` tags. The workflow never pushes directly to `master`.
3. Review and update `docs/changelog/current.md` on `master` using the four required categories. Each bullet is limited to 100 characters.
4. Open **Actions > Publish Windows installer > Run workflow** on `master`. Choose `minor` (default), `secondary`, or `major`.
5. GitHub bumps the selected version, freezes its changelog, tests and smoke-tests the Windows installer, then publishes the installer, checksum, and release notes to this repository's Releases page.
6. GitHub opens a release-record PR and explicitly starts its CI checks. **Merge that PR manually before the next release** so `master` matches the published version.

Before the first release, enable **Settings > General > Releases > Enable release immutability** to protect published tags, notes and assets. If a release run fails, check its logs and inspect any leftover draft release or branch before retrying. Existing local builds remain version-neutral unless you pass `-Minor`, `-Secondary`, or `-Major`; they do not publish releases.

After launching, open a PDF with **Ctrl+O** or drop one onto the welcome screen. Use **Ctrl+F** to search, **Ctrl+S** to save, or **File > Save as** to write a separate copy.

### Build and OCR prerequisites

- Install **Inno Setup 6** before running `build.cmd`. The installer is written to `dist/installer/Simple-PDF-Setup-vX.Y.Z-x64.exe` using the checked-out version.
- **OCR requires Tesseract.** PyMuPDF uses the Tesseract engine built into MuPDF, but needs Tesseract language data (`eng.traineddata` for English). For source runs, install Tesseract OCR with English language data and, if PyMuPDF cannot locate it, set `TESSDATA_PREFIX` to the folder containing `eng.traineddata` (for example, `C:\Program Files\Tesseract-OCR\tessdata`). The Tesseract command-line executable is not called when the data path is provided.
- For a local installer build, put `eng.traineddata` in `installer/tessdata/` before building. The manually triggered GitHub release workflow downloads it automatically.

## Important limitations

- Text boxes are editable annotations; Simple PDF does **not** modify existing page text in place.
- Drawn or image signatures are visual marks, **not** certificate-based digital signatures.
- Find and selection use local OCR on scanned pages when Tesseract English data is installed. Recognition may take longer on large documents and may miss unclear text. OCR text is not embedded into saved PDFs.
- **Redacted output is image-only:** Text selection, links, forms, signatures and vector detail are not preserved in the new copy. The original stays unchanged. Review all regions, particularly scanned text: OCR can miss matches. Protected, signed and damaged PDFs are refused.

See [backlog.md](backlog.md) for proposed work, not shipped features.

## PDF file association

The Windows installer registers Simple PDF as a PDF handler and refreshes Explorer's file associations. After installing, select **Set as default PDF app** on the welcome screen or under **File**. This opens Windows **Settings > Apps > Default apps**. On supported Windows 11 versions, Simple PDF's settings open directly; otherwise find `.pdf` and select **Simple PDF**. Once selected, double-clicking PDF files in Explorer opens them in Simple PDF.

Windows controls the default app. Installation and the button never change your preference automatically. Running from source does not register the app; use the installer before selecting it. You can change your default PDF app again at any time through Windows Settings.

## Contributing

When `master` changes, GitHub Actions rebases same-repository PR stacks in dependency order. A conflict gate blocks Windows CI until a PR merges cleanly with its base. Conflicting rebases require manual resolution; fork PR branches are not force-pushed. CI is explicitly restarted after bot rebases.

See [AGENTS.md](AGENTS.md) for the architecture, testing requirements, commit and PR conventions, and change-log rules.

See [distribution guidance](docs/distribution.md) for software-directory listing details and WinGet submission steps.
