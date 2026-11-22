# REDACT-01: Secure PDF redaction implementation plan

Status: Planned, not implemented
Updated: 2026-11-22
Priority: High

## Goal and security boundary

Remove user-selected information from the *exported PDF's underlying content*, then cover its former location with an opaque black rectangle. A visual overlay is not redaction. Retain the original PDF unchanged. Only describe an output as verified after a complete, independent reopen-and-inspect pass. When verification coverage is incomplete, fail closed and give a specific reason.

The guarantee applies to the new output PDF, not copies of the original, backups, cloud history, filesystem snapshots, clipboard contents, or temporary files created by other software. No arbitrary PDF can be guaranteed safe solely from a keyword search or OCR result; unsupported or ambiguous cases must be refused rather than silently accepted.

## User experience

### 1. Search by information

- Add **Tools > Redact information** and an optional toolbar action.
- Show a dialog asking: **What information would you like to redact?**
- Support an exact text/phrase input and case-sensitive and whole-word options. Do not log, persist, or send the term anywhere.
- Search all pages using existing text layers; when native text is absent, offer local OCR with coordinate-aware results. Explicitly label OCR matches and recognition uncertainty.
- Report match count; show page number, small local context, and highlight every matching location, including wrapped/rotated text. No hits must be reported as **No matches**, never **Document is safe**.
- Default to all matches selected, but allow individually deselecting matches and review before applying.
- Flag likely duplicate sensitive values outside searchable page text, including forms and annotations, and either handle them securely or block the export.

### 2. Select and right-click

- Support ordinary existing-page text selection with left-mouse drag. Right-click a text selection and show **Redact selection**.
- Support rectangular region selection for image, handwritten, or mixed content. Right-click a completed region and show **Redact area**. The contextual action may also be offered when selecting an existing editable item, but must remove its associated PDF object/content rather than merely deleting an overlay.
- Reuse the canvas page-coordinate conversion and visible-selection style. A visible preview must precisely match the PDF regions that will be processed.
- The current canvas renders pages as pixmaps, so it needs selectable text geometry and hit testing (character/word quads). Existing annotation selection is not equivalent to selecting embedded page text.
- Preserve normal selection/dragging of editable items. Do not allow the existing right-click-to-cancel placement gesture to swallow the completed-selection context menu; right-click and Escape cancel only an *unfinished* selection or placement.
- An active selection, target page and review state must belong to the active document tab. Clear pending targets if the page/document content changes or a tab closes.

### 3. Review and confirm

- Both entry points create the same pending redaction targets, with page number, source type, bounding quads/rectangles and document revision.
- Show an on-canvas temporary preview and a review dialog with selected occurrence count, page list and the affected area.
- Explicitly warn: **Redaction permanently removes content from the exported copy and can invalidate existing digital signatures.**
- Buttons: **Cancel** and **Redact and save copy**. No direct overwrite of the source in the first release.
- After successful verification, offer to open the redacted copy and show a concise verification report. Never label preview rectangles or annotation marks as final redaction.
- A search selection can span multiple pages. Rectangle selection is per page; several target rectangles can be queued.

## Architecture and implementation

Keep PySide6 UI components as coordinators. Add focused, independently tested services:

- `RedactionMatchService`: extract native text matches and exact page quads, integrate a coordinate-aware OCR text page, and resolve user text/area selections to targets. Match semantics should be tested with Unicode, ligatures, case, hyphenation and line breaks.
- `RedactionPlan`: immutable targets containing page, quads/rects, reason/type and source-document revision/fingerprint. Reject stale or empty plans. Explicitly track unsupported content and match coverage.
- `RedactionService`: on a **separate working document**, call `Page.add_redact_annot()` and `Page.apply_redactions()` with explicitly selected text/image/vector policies. Never use a black drawing annotation as the only removal action.
- `RedactionOutputWriter`: create a fresh full PDF save with aggressive garbage collection and stream cleanup. Never call `saveIncr()`, use an incremental update, or retain old xref revisions. Write privately to a temporary output, reopen/verify, then atomically publish the selected new path.
- `RedactionVerifier`: reopen using PyMuPDF and at least one independent extraction/inspection path in CI; check targeted page text, OCR layers, images, objects, streams, hidden content, annotations, forms, metadata, attachments and any old revisions that the saved output might expose. Surface a structured pass/fail/unsupported report.

Investigate PyMuPDF's `PDF_REDACT_IMAGE_PIXELS` behavior for shared images: the newly generated visible pixels may be sanitized while a referenced original image or duplicate sensitive object survives in the output. A redaction is safe only if surviving resource references and hidden/unreferenced objects cannot expose the target. Sanitize all necessary copies or refuse the output. Treat reused images on other pages as a cross-page leak risk.

Use the strongest content-removal settings compatible with the selected region, including intersecting text, vector content and covered image pixels. Review potential collateral removal at glyph boundaries. Sanitize metadata, attachments, JavaScript, hidden text, links, form data, annotations and thumbnails under a documented policy; if keeping them cannot be verified safe, remove them with explicit user consent or refuse. Do not silently strip unrelated fields or alter permitted content without disclosure.

Password-protected PDFs require sufficient authorization and an explicit output-encryption policy. Signed PDFs require a warning or refusal, because a full rewrite invalidates existing cryptographic signatures. Keep existing sessions/source files unchanged on failure; prevent sensitive values from being written to logs, crash reports or persistent preferences.

References:
- PyMuPDF redaction: https://pymupdf.readthedocs.io/en/latest/page.html
- PyMuPDF save/scrub: https://pymupdf.readthedocs.io/en/latest/document.html

## Safety-critical acceptance criteria

- Selected native text is absent from saved extraction, search and copy/paste, and redacted pixels are black in rendered output.
- Region-based redaction removes overlapping scan/image content and accessible OCR text layers, not only drawn rectangles.
- No targeted value remains in form fields, annotations, document properties, embedded files, hidden/reused resources or old incremental revisions within the output PDF.
- Search results highlight exactly the regions applied; unsupported matching (including ambiguous OCR) is reported, not guessed.
- Full rewrites do not publish a result until verification passes. Failed verification preserves the source and any existing destination.
- Verification includes independent extraction plus rendering/reopen checks; it must not rely only on the same `page.search_for()` used to find candidates.
- Cross-page matching, selection and right-click context actions remain isolated between tabs.
- No claim is made that originals, backups or pre-existing copies have been erased.

## Test matrix

- Native multi-page text: repeated terms, case sensitivity, Unicode, wrapped text, ligatures, overlap with adjacent glyphs and rotated pages.
- UI: search dialog, no-result message, match highlighting, per-match opt-out, native text selection, rectangle selection, context menus, cancel, Escape, zoom, tab switch and edit-state invalidation.
- Images: pure scans, text+image layers, OCR false negatives, shared image XObjects, clipping, transparency and vector content.
- Hidden data: duplicate streams, incremental revisions, attached files, document information, XMP metadata, hidden text, annotations, AcroForm fields, JavaScript, thumbnails and links.
- Security: passwords, permissions, encryption preservation policy, existing cryptographic signatures, truncated/malformed PDFs and unrecognized PDF structures.
- Output: no incremental save, validation after reopen, external extraction and render check, atomic output publication, no source mutation, output collision, cancellation, failed writes and cleanup.
- Performance: large documents and many hits, progress reporting, cancellation, and responsiveness.

## Reviewable implementation stages

1. **REDACT-01A: Selection and targeting**. Add page-text geometry, multi-page candidate finder, rectangle/text selection and context-menu signals; keep actual redaction commands unavailable until safe engine integration.
2. **REDACT-01B: Secure redaction engine**. Add an isolated service for applying content redactions, a full rewrite writer and safety-focused test fixtures; no silent success.
3. **REDACT-01C: Verification and sanitization**. Add output validation, metadata/attachments/forms/resource policy, independent checks and fail-closed handling.
4. **REDACT-01D: End-to-end UI and OCR**. Connect search popup, right-click actions, preview, confirmation and verified save; test scanned PDFs and cross-tab behavior.

Implement these as focused stacked PRs according to `AGENTS.md`; do not merge automatically. The feature is releasable only when all stages and safety-critical tests are complete.
