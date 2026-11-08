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

## Development

Requires Python 3.12+.

```powershell
python -m pip install -e ".[dev]"
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
python -m sabl_pdf.main
```

Windows build (Inno Setup 6 required):

```powershell
./scripts/build.ps1
```

For OCR in a source checkout, install Tesseract `eng.traineddata` or provide a valid `TESSDATA_PREFIX`. Release installers include English OCR data.

## PDF association

The installer registers SABL PDF as an available PDF handler. Windows 10/11 require the user to choose the default PDF app through **Settings > Apps > Default apps**. SABL PDF never changes the default silently.

## Contributing

See [AGENTS.md](AGENTS.md) for architecture, tests, atomic commit rules, stacked PR workflow and daily change logs.
