# Unreleased

First public release. This draft covers the history of changes included in the build.

## New features
- Open, view, and save PDF documents locally without uploading files to a service.
- Display all PDF pages in one scrollable view with zoom and page navigation.
- Search existing PDF text, highlight matches, navigate results, and copy selected text.
- Open multiple PDFs in tabs with independent page, zoom, search, and editing state.
- Indicate unsaved changes and offer Save, Discard, or Cancel before closing a tab.
- Reopen an existing file in its current tab rather than creating a duplicate.
- Browse pages with a collapsible thumbnail sidebar and synchronised page selection.
- Use a persistent Find bar with match counts, next/previous navigation, and typed search.
- Access common commands from a grouped quick-access toolbar and compact page controls.
- Customise toolbar buttons, reset the layout, and use editing keyboard shortcuts.
- Open PDFs using a welcome screen, the file picker, or drag and drop.
- Add, edit, select, reposition, and delete editable PDF text boxes.
- Fill supported PDF text fields and checkbox forms.
- Draw signatures or import PNG/JPEG signatures and place them on a PDF.
- Reuse locally saved drawn signatures without drawing them again.
- Highlight and underline PDF text and add editable note annotations.
- Click to select placed text, signatures, markup, or notes; drag or delete them.
- Move placed items between pages, preserving their editability and appearance.
- Preview text boxes, signatures, notes, and markup at the pointer before placement.
- Cancel an uncommitted placement with right-click or Escape.
- Merge PDF documents or split them into selected page ranges.
- Delete, rotate, and reorder PDF pages.
- Optimise PDF objects and optionally recompress images into a separate output file.
- Convert image files into PDF pages and export PDF pages as PNG images.
- Recognise scanned-page text locally with Tesseract OCR and export a TXT file.
- Install SABL PDF with a Windows installer and register it as an available PDF reader.
- Run, test, and build SABL PDF with double-click Windows command launchers.

## Bugfixes
- Make Save target the new file after a Save As operation.
- Keep the open PDF unchanged when creating a compressed copy.
- Allow single-click text box placement and drag-to-size placement.
- Let right-click cancel unfinished text box placement without saving content.
- Correct the placement, preview, cancellation, and reuse of drawn signatures.
- Show one warning for damaged PDFs instead of repeated MuPDF errors.
- Load readable portions of damaged PDFs without overwriting the original.
- Keep the previously open document when an invalid PDF is selected.
- Correct PDF page dimensions and navigation in continuous scrolling.
- Keep annotation operations stable when loading and inspecting pages.
- Preserve placed annotations when dragging across PDF pages.
- Support edge-scrolling toward destination pages and reject invalid drops.
- Find Inno Setup reliably when the Windows build script runs.
- Let the first GitHub Release proceed without a previously published release.
- Resolve PySide6 imports during Windows release type checks using the installed virtual environment.

## Performance improvements
- Render pages near the visible PDF viewport instead of all pages at once.
- Render page thumbnails lazily when needed for navigation.
- Debounce typed searches to avoid searching the entire document on every keystroke.

## Documentation
- Document how to install, run, test, and build SABL PDF on Windows.
- Explain local OCR dependencies and setup for Tesseract language data.
- Describe PDF file association and Windows default-app selection.
- Clarify annotation-based text editing and the limits of visual signatures.
- Explain OCR output limits and why permanent redaction is not yet supported.
- Document contributor rules for tests, pull requests, and release history.
- Describe manual GitHub Actions releases, version selection, and changelog handling.
- Keep planned features in a separate backlog rather than release notes.
