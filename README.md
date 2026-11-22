# SABL PDF

A small, offline Windows PDF viewer and editor written in Python.

No account. No advertising. No telemetry. No subscriptions.

## Features

- **Viewer:** Open, search, zoom and copy text.
- **Text & forms:** Add/edit/remove text-box annotations; fill interactive PDF text or checkbox fields.
- **Signatures:** Draw a signature or place a PNG/JPEG signature image.
- **Pages:** Merge, split, delete, rotate or reorder pages.
- **Annotations:** Highlight, underline, add notes or remove annotations.
- **Compression:** Optimise PDF object streams; optionally recompress images. Results depend on the document.
- **Conversion:** Images to PDF and PDF pages to PNG.
- **OCR:** Extract text from scanned pages locally using Tesseract data installed with the Windows package.

Existing PDF page text is not edited in-place. Newly added text remains editable until the annotation is flattened externally. Signatures are visual marks, not certificate-based digital signatures.

## Local development on Windows

Requires Python 3.12+ installed and available through `py` or `python`. Double-click these files in the repository root:

| File | Action |
| --- | --- |
| `run.cmd` | Create or reuse `.venv`, install dependencies, and open SABL PDF. |
| `test.cmd` | Prepare the environment, run pytest, compile Python files, and run Ruff and Pyright. |
| `build.cmd` | Run all checks, package the app with PyInstaller, and create the Windows installer. |

`build.cmd` requires Inno Setup 6. The installer output is in `dist/installer`.

To run the same tasks from PowerShell, use `./scripts/run.ps1`, `./scripts/test.ps1`, or `./scripts/build.ps1`. A double-click on a `.ps1` file normally opens an editor on Windows, so the `.cmd` launchers invoke the scripts with a process-scoped execution policy. No permanent PowerShell policy change is made. Tests use Qt offscreen mode without affecting the normal app launcher.

The type check also runs directly with `python -m pyright` after installing `.[dev]`. Existing files with type errors are listed under `[tool.pyright].ignore` so Pyright can gate clean files and new modules. Remove each entry when its typing is fixed.

For OCR in a source checkout, install Tesseract `eng.traineddata` or provide a valid `TESSDATA_PREFIX`. Release installers include English OCR data.

## PDF association

The installer registers SABL PDF as an available PDF handler. Windows 10/11 require the user to choose the default PDF app through **Settings > Apps > Default apps**. SABL PDF never changes the default silently.

## Contributing

See [AGENTS.md](AGENTS.md) for architecture, tests, atomic commit rules, stacked PR workflow and daily change logs.
