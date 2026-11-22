# SABL PDF

An offline PDF viewer and editor for Windows, built with Python, PySide6 and PyMuPDF. No account, ads, telemetry or subscription.

## Features

- **Viewing:** Open PDFs in separate tabs, search existing text, zoom, use page thumbnails and copy text.
- **Text and forms:** Add, edit, move or remove text-box annotations; fill PDF text and checkbox fields.
- **Signatures:** Draw and reuse a signature, or place a PNG/JPEG signature image.
- **Pages:** Merge PDFs, split page ranges, delete, rotate or reorder pages.
- **Annotations:** Highlight, underline, add notes and remove annotations.
- **Compression:** Optimise PDF object streams and optionally recompress images. Savings depend on the file.
- **Conversion:** Add images as PDF pages or export PDF pages as PNG files.
- **OCR:** Recognise scanned-page text locally and export it as text.

## Run from source (Windows)

Requires **Python 3.12+** available as `py` or `python`. From a checkout, double-click `run.cmd`, or use the commands below in the repository root:

| Launcher | What it does |
| --- | --- |
| `run.cmd` | Creates/reuses `.venv`, installs project and development dependencies, and opens the app. |
| `test.cmd` | Prepares the environment, then runs pytest, Python compilation and Ruff. |
| `build.cmd` | Runs checks, builds the app with PyInstaller and creates the installer with Inno Setup 6. |

The PowerShell equivalents are `./scripts/run.ps1`, `./scripts/test.ps1` and `./scripts/build.ps1`. The `.cmd` launchers are intended for double-clicking; they invoke PowerShell without requiring a permanent execution-policy change. Tests use Qt offscreen mode.

After launching, open a PDF with **Ctrl+O** or drop one onto the welcome screen. Use **Ctrl+F** to search, **Ctrl+S** to save, or **File > Save as** to write a separate copy.

### Build and OCR prerequisites

- Install **Inno Setup 6** before running `build.cmd`. The installer is written to `dist/installer/SABL-PDF-Setup.exe`.
- OCR requires Tesseract language data. For source runs, install English `eng.traineddata` and configure `TESSDATA_PREFIX` if needed.
- For a local installer build, put `eng.traineddata` in `installer/tessdata/` before building. The tagged-release workflow downloads this file for its installer build.

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
