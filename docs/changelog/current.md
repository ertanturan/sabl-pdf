# Unreleased

First public release of SABL PDF. Includes features and fixes implemented since the project began; this is not limited to the changes from the last build.

## New features
- Open, view, and save PDF files locally, with zoom, selectable text, copy, search, and continuous multi-page scrolling.
- Open multiple PDFs in tabs with independent view and editing state, duplicate-file detection, unsaved-change indicators, and save/discard/cancel prompts when closing.
- Navigate pages using a collapsible thumbnail sidebar that tracks the active page.
- Find text using a persistent search bar with highlighted results, match counts, next/previous controls, and debounced input.
- Access frequently used tools from a quick-access toolbar, customise its buttons, reset its layout, and use editing shortcuts.
- Start from a welcome screen that opens PDFs through the file picker or drag and drop.
- Add, edit, reposition, and remove text boxes; fill supported PDF text and checkbox form fields.
- Draw visual signatures, import signature images, place them on pages, and reuse locally saved drawn signatures. These are visual marks, not certificate-based signatures.
- Highlight or underline text, place notes, and select, move, or delete editable annotations and other placed items.
- Preview text boxes, signatures, notes, and text markup at the pointer before placement; cancel unfinished placement with right-click or Escape.
- Drag placed text boxes, signatures, notes, and markup between PDF pages while preserving editable content.
- Merge, split, delete, rotate, and reorder PDF pages.
- Optimise PDFs with optional image recompression, saving the result to a separate file.
- Convert images into PDF pages and export PDF pages as PNG images.
- Recognise text on scanned pages locally with Tesseract OCR and export it as a text file. OCR does not yet add a searchable PDF text layer.
- Install the Windows desktop application with Inno Setup and register it as an available PDF handler without changing the user's default app.

## Bugfixes
- Subsequent Save operations use the new destination after Save As.
- Preserve the open PDF when creating a compressed output.
- Allow a click to place a default-sized text box, or a drag to size it; right-click cancels without adding content.
- Fix drawn signature placement, cursor preview, cancellation, and reuse from the signature controls.
- Open readable portions of damaged PDFs with one warning instead of repeated MuPDF errors; invalid files leave the previously open document intact.
- Correct continuous scrolling and page dimensions across multi-page PDFs.
- Keep annotation operations stable while pages are being inspected or edited.
- Allow cross-page dragging of placed items, including scrolling to offscreen destination pages, and reject invalid drops.
- Resolve the Inno Setup executable reliably when building on Windows.

## Performance improvements
- Render PDF pages near the visible viewport instead of drawing every page at once.
- Render page thumbnails on demand as they become needed.
- Debounce text searches while typing to avoid repeated full searches for each keystroke.

## Documentation
- Document Windows installation, running, testing, building, OCR setup, and PDF file associations.
- Explain current editing limits, the difference between visual and digital signatures, OCR limitations, and the absence of permanent redaction.
- Add concise contributor guidance for branch stacking, PR descriptions, tests, and release records.
- Document the manual GitHub Actions installer release process with automatic version selection and version-specific changelogs.
- Maintain a separate backlog and design plans for features not yet shipped, without listing them as released capabilities.
