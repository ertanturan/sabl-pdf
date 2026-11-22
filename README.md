# SABL PDF

SABL PDF is a Windows desktop app for opening, reviewing and making common changes to PDF files without uploading documents to a service. You can work with several PDFs in tabs, fill forms, add text and signatures, annotate pages, reorganise pages and save the result locally.

It runs offline and requires no account or subscription. It does not include advertising or telemetry.

## Tech Stack

- **Python 3.12+** for the application and PDF services.
- **PySide6 (Qt)** for the Windows desktop interface.
- **PyMuPDF** for PDF rendering, text extraction and document operations.
- **Pillow** for image handling; **Tesseract OCR** for scanned-page text recognition through PyMuPDF.
- **PyInstaller** for executable packaging and **Inno Setup 6** for the Windows installer.

## Features

- **Viewing:** Open PDFs in separate tabs, search existing text, zoom, use page thumbnails and copy text.
- **Text and forms:** Add, edit, move or remove text-box annotations; fill PDF text and checkbox fields.
- **Signatures:** Draw and reuse a signature, or place a PNG/JPEG signature image.
- **Pages:** Merge PDFs, split page ranges, delete, rotate or reorder pages.
- **Annotations:** Highlight, underline, add notes and remove annotations.
- **Compression:** Optimise PDF object streams and optionally recompress images. Savings depend on the file.
- **Conversion:** Add images as PDF pages or export PDF pages as PNG files.
- **OCR:** Recognise scanned-page text locally using Tesseract OCR and export it as text. Tesseract OCR support and language data must be available.

## Run from source (Windows)

Requires **Python 3.12+** available as `py` or `python`. From a checkout, double-click `run.cmd`, or use the commands below in the repository root:

| Launcher | What it does |
| --- | --- |
| `run.cmd` | Creates/reuses `.venv`, installs project and development dependencies, and opens the app. |
| `test.cmd` | Prepares the environment, then runs pytest, Python compilation and Ruff. |
| `build.cmd` | Checks the existing version, runs tests, builds with PyInstaller and creates the Windows installer. |

The PowerShell equivalents are `./scripts/run.ps1`, `./scripts/test.ps1` and `./scripts/build.ps1`. The `.cmd` launchers are intended for double-clicking; they invoke PowerShell without requiring a permanent execution-policy change. Tests use Qt offscreen mode.

### Build version numbers

The manually triggered GitHub release workflow increments the version automatically. SABL uses `x.y.z` with `x` as major, `y` as secondary and `z` as minor. Ordinary local and CI builds preserve their current version.

| Command | Example from `0.1.9` |
| --- | --- |
| GitHub Actions release: `minor` (default) | `0.1.10` |
| GitHub Actions release: `secondary` | `0.2.0` |
| GitHub Actions release: `major` | `1.0.0` |
| `build.cmd` (normal local build) | `0.1.9` |

### Publish a Windows installer

The release action is **manual only**. After this workflow is merged into `master`:

1. Create a separate **public** repository called `ertanturan/sabl-pdf-releases`; the SABL source repository is private.
2. Add a GitHub Actions secret called `PUBLIC_RELEASE_TOKEN` to the private source repository. Use a fine-grained token with Contents read/write permission limited to the public releases repository. Allow GitHub Actions to create PRs, and ensure repository rules allow the release bot to push release branches and tags.
3. Edit `docs/changelog/current.md` on `master` to describe what is shipping. Use the four required categories.
4. Open **Actions > Publish Windows installer > Run workflow** on the `master` branch and choose `minor`, `secondary` or `major`. The default is `minor`.
5. GitHub validates changelog history, increases the selected component, runs the tests, builds and smoke-tests the installer, generates its SHA-256 checksum, and publishes a versioned installer with only this release's notes to the public distribution repository.
6. GitHub opens a release-record PR back to the private source repository. **Merge this PR manually before starting another release**, keeping project versions and changelog history in sync.

A failed workflow does not publish a successful release automatically; a staged draft or release branch may require manual inspection. Check the run's results before sharing a download.

A local `build.cmd` does not publish a release or increment any component by default. For an explicit local version change, `build.cmd -Minor`, `build.cmd -Secondary` or `build.cmd -Major` remain available, and `build.cmd -NoVersionBump` explicitly preserves the version. A local change must be committed through a PR before an official GitHub release. The tagged source commit and release snapshots must stay unchanged.

After launching, open a PDF with **Ctrl+O** or drop one onto the welcome screen. Use **Ctrl+F** to search, **Ctrl+S** to save, or **File > Save as** to write a separate copy.

### Build and OCR prerequisites

- Install **Inno Setup 6** before running `build.cmd`. The installer is written to `dist/installer/SABL-PDF-Setup-vX.Y.Z-x64.exe` using the checked-out version.
- **OCR requires Tesseract.** PyMuPDF uses the Tesseract engine built into MuPDF, but needs Tesseract language data (`eng.traineddata` for English). For source runs, install Tesseract OCR with English language data and, if PyMuPDF cannot locate it, set `TESSDATA_PREFIX` to the folder containing `eng.traineddata` (for example, `C:\Program Files\Tesseract-OCR\tessdata`). The Tesseract command-line executable is not called when the data path is provided.
- For a local installer build, put `eng.traineddata` in `installer/tessdata/` before building. The manually triggered GitHub release workflow downloads it automatically.

## Important limitations

- Text boxes are editable annotations; SABL PDF does **not** modify existing page text in place.
- Drawn or image signatures are visual marks, **not** certificate-based digital signatures.
- OCR can extract text, but does **not** yet make scanned PDFs searchable within the PDF. Normal Find searches an existing text layer.
- **Permanent redaction is not available yet.** Covering text with an annotation does not securely remove the underlying data.

See [backlog.md](backlog.md) for proposed work, not shipped features.

## PDF file association

The installer registers SABL PDF as an available PDF app. On Windows 10/11, select it through **Settings > Apps > Default apps** if you want it as the default. Installation does not change your preference automatically.

## Contributing

See [AGENTS.md](AGENTS.md) for the architecture, testing requirements, commit and PR conventions, and change-log rules.
