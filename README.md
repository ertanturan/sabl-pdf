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

## Using the workspace

- Open a PDF with **Ctrl+O** or drag it onto the welcome screen.
- Open multiple PDFs in tabs. Each tab keeps its own page, zoom, search and edits. Use **Ctrl+W** to close a tab. SABL asks whether to save unsaved changes.
- Use the quick-access toolbar for **Open**, **Save**, **Find**, **Add Text**, **Highlight**, **Sign**, **Rotate** and **Compress**.
- Show or hide buttons through **View > Customize toolbar**. **Reset toolbar** restores the default arrangement.
- Click **Find** or use **Ctrl+F** to see matching text and move between matches.
- Use the **Pages** sidebar to jump to pages. Close the sidebar when you want more reading space.
- While placing text, annotations or signatures, click or drag on a page. Press **Escape** or right-click to cancel placement.

| Shortcut | Action |
| --- | --- |
| Ctrl+O | Open another PDF |
| Ctrl+S | Save the current PDF |
| Ctrl+W | Close the current tab |
| Ctrl+F | Find text in the current PDF |
| Ctrl+Shift+T | Add a text box annotation |
| Ctrl+Shift+H | Highlight an area |
| Ctrl+Alt+S | Draw and place a visual signature |
| Ctrl+Shift+R | Rotate the current page |
| Ctrl+Shift+C | Compress to a separate PDF file |
| Escape | Cancel placement or close Find |

The **Sign** toolbar action creates a drawn signature mark, not a certificate-based digital signature. Native text editing and permanent redaction are separate planned features.

## Local development on Windows

Requires Python 3.12+ installed and available through `py` or `python`. Double-click these files in the repository root:

| File | Action |
| --- | --- |
| `run.cmd` | Create or reuse `.venv`, install dependencies, and open SABL PDF. |
| `test.cmd` | Prepare the environment, run pytest, compile Python files, and run Ruff. |
| `build.cmd` | Run all checks, package the app with PyInstaller, and create the Windows installer. |

`build.cmd` requires Inno Setup 6. The installer output is in `dist/installer`.

To run the same tasks from PowerShell, use `./scripts/run.ps1`, `./scripts/test.ps1`, or `./scripts/build.ps1`. A double-click on a `.ps1` file normally opens an editor on Windows, so the `.cmd` launchers invoke the scripts with a process-scoped execution policy. No permanent PowerShell policy change is made. Tests use Qt offscreen mode without affecting the normal app launcher.

For OCR in a source checkout, install Tesseract `eng.traineddata` or provide a valid `TESSDATA_PREFIX`. Release installers include English OCR data.

## PDF association

The installer registers SABL PDF as an available PDF handler. Windows 10/11 require the user to choose the default PDF app through **Settings > Apps > Default apps**. SABL PDF never changes the default silently.

## Contributing

See [AGENTS.md](AGENTS.md) for architecture, tests, atomic commit rules, stacked PR workflow and daily change logs.
