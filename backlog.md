# SABL PDF Backlog

Status: Planned
Last reviewed: 2026-11-08
Scope: The ten feature areas below are the only planned feature additions for now. This file describes proposed work, not completed functionality. Current import and signature-placement bug fixes are tracked separately.

## Product and delivery rules

- Windows desktop, Python 3.12+, PySide6 and PyMuPDF; local and offline by default.
- Keep PDF operations in small, independently testable services. Each method should perform one unit of work; UI components coordinate services.
- Deliver each backlog item in its own focused feature PR, with tests. Split large items into separately reviewable implementation stages within their feature branch when needed.
- Keep source PDFs unchanged until a user explicitly saves. For recovery, redaction, compression, encryption and signing, default to saving a new output file unless an operation can be proven safe.
- Preserve encryption, signatures, permissions, annotations and form values when the selected operation allows it. Otherwise warn or refuse instead of silently discarding them.
- Keep search, rendering, editing and file operations responsive on large documents. Support cancellation for long operations.
- Do not copy GPLv3 KillerPDF implementation into SABL; build on SABL's Python services and separately reviewed dependencies.
- Definition of done for each item: relevant unit and integration tests, Windows UI smoke coverage, error cases, documentation and a reproducible manual test.
- Follow `AGENTS.md` for stacked branches, PR descriptions and changelogs. Do not merge PRs automatically.

## Recommended implementation order

| Order | ID | Feature | Priority | Size | Dependency |
| --- | --- | --- | --- | --- | --- |
| 1 | TAB-01 | Multiple tabs | High | M | Existing session and viewer |
| 2 | PASS-01 | Password protection | High | M | Document session and safe saves |
| 3 | OCR-01 | Searchable OCR and in-file search | High | M/L | Viewer search and current OCR |
| 4 | COMP-01 | Advanced compression | Medium | M | Existing compression service |
| 5 | REPAIR-01 | PDF repair and recovery | High | L | Document open/save, PASS-01 for protected files |
| 6 | DIFF-01 | PDF comparison | Medium | L | TAB-01 |
| 7 | REDACT-01 | Permanent redaction | High | L | PASS-01, safe output and verification |
| 8 | TEXT-01 | Advanced text editing | Medium | XL | Text extraction and page geometry |
| 9 | REPLACE-01 | Find and replace | Medium | L | TEXT-01, OCR-01 for scanned search |
| 10 | SIGN-01 | Certificate-based digital signatures | Medium | XL | PASS-01, signature-safe saves |

Size: M = moderate; L = large; XL = particularly complex. Priorities indicate importance, while order also accounts for dependencies. Bug fixes already in flight take precedence over feature work.

## TAB-01: Multiple tabs

**Current state:** `MainWindow` owns a single `DocumentSession`, canvas, viewer and set of document services.

**User experience**
- Open each PDF in its own tab; switch, reorder and close tabs.
- Keep page, zoom, selection, search result and unsaved state per tab.
- Show a modified marker; ask to Save, Discard or Cancel when closing a dirty tab or exiting.
- Reopening the same path should focus its existing tab, not silently open duplicate editing sessions.

**Implementation**
- Introduce a document-tab controller/model holding `DocumentSession`, its services, canvas state and lifetime.
- Make actions use the active tab instead of a global document.
- Scope background tasks, save paths and errors to the tab that started them.

**Acceptance**
- Edits in one tab never alter another; switching tabs preserves navigation and selections.
- Closing a tab cleans up its document and does not close other tabs.
- Closing multiple dirty tabs cannot silently lose work.
- Tests cover tab isolation, duplicate open, active actions, cancellation and close prompts.

## PASS-01: Open, save and protect password-secured PDFs

**Current state:** `DocumentSession.open()` does not request a password; save paths do not explicitly preserve source encryption.

**User experience**
- Prompt for a password when an encrypted PDF is opened, with retry and cancel.
- Show whether opening granted user or owner permissions; respect restrictions on modifying, printing and exporting.
- Offer Save a Protected Copy with user/owner password, AES-256 and configurable permissions.
- Offer Remove Protection only with sufficient authorization.

**Implementation**
- Add a dedicated document-security service using PyMuPDF authentication and save encryption options.
- Persist authorization state per document session, but never persist plaintext passwords.
- Centralize permission checks for edit, extract, save and future features.
- Preserve encryption by default when saving protected PDFs; use atomic output publication.

**Acceptance**
- Correct password opens; incorrect or canceled password leaves existing tabs unchanged.
- Protected Save and Save As reopen with the expected permissions.
- Restricted operations are blocked with specific messages; passwords never appear in logs.
- Tests cover user/owner passwords, encryption preservation, failed attempts and permissions.

## OCR-01: Searchable OCR and in-file search

**Current state:** OCR extracts text from a page and exports TXT. `ViewerService.search()` only searches an existing PDF text layer, so scanned PDF text is not searchable through normal Find.

**User experience**
- Ctrl+F opens a persistent search bar with next/previous result, match count and page highlighting.
- Search native text immediately; offer OCR for scanned pages and include recognized words in the same results.
- Add Make PDF Searchable to save a PDF with a selectable, searchable OCR text layer, without requiring a separate TXT export.
- Show progress, cancel, and warn about uncertain recognition or unsupported layout.

**Implementation**
- Add a per-document, per-page OCR text-page cache used by searching; invalidate on page edits or replacement.
- Extend the search service to distinguish native and OCR hits and return accurate coordinates.
- Investigate PyMuPDF's OCR PDF output and validate a safe text-layer creation strategy before promising layout preservation. Avoid silently rasterizing native-text pages or dropping annotations.
- Run OCR off the UI thread, reuse bundled Tesseract data, and expose searchable-copy output as an explicit action.

**Acceptance**
- Search returns highlighted matches across text-only, scanned and mixed PDFs.
- Saved searchable PDFs reopen in SABL and another reader with the recognized text searchable/selectable.
- No duplicate native/OCR matches, stale caches, silent loss of links/forms, or original-file overwrites.
- Tests cover scans, rotations, multiple pages, empty/failed OCR, cancellation and output reopening.

## COMP-01: Advanced compression

**Current state:** `CompressionService.optimise()` already does object-stream optimization and optional image recompression.

**User experience**
- Presets: Lossless, Balanced and Smallest File, plus advanced image-quality control.
- Before saving, show original size, proposed output size and percentage change.
- Warn if the output is larger or image quality will be reduced; never promise a fixed reduction.

**Implementation**
- Keep lossless object cleanup separate from explicit lossy image rewriting.
- Apply image recompression only for user-approved settings; preserve vector text, form values and annotations.
- Write to a temporary destination, validate output by reopening it, then publish safely.
- Handle protected and signed input without stripping security or silently invalidating signatures.

**Acceptance**
- Lossless mode keeps extractable text and page count unchanged.
- Lossy mode visibly labels the quality tradeoff; output opens and page images render.
- Oversized/no-benefit and failed compression paths preserve the input and existing destination.
- Tests cover image-heavy, text-only, protected, signed and malformed PDFs.

## REPAIR-01: PDF repair and recovery

**Current state:** `DocumentSession` detects some repair warnings and keeps the source intact, but lacks a guided repair flow. Users have observed missing cross-reference object errors.

**User experience**
- Open readable pages even if other pages are damaged, with per-page error details.
- Offer Analyze Damage and Save Recovered Copy, with a summary of skipped or replaced objects/pages.
- Retry or skip damaged content without repeatedly displaying raw MuPDF warnings.
- Refuse unsafe recovery when encryption, certificate signatures or document integrity cannot be preserved.

**Implementation**
- Isolate parsing/rendering errors per page and collect structured diagnostics.
- Use PyMuPDF's existing repair signals first; evaluate bounded fallback recovery only when needed.
- Save recovery output to a new file, reopen it and verify page count and readable content.
- Never fabricate missing content or report partial recovery as complete.

**Acceptance**
- Missing xref objects do not crash the UI or overwrite the original.
- A user can distinguish recovered pages, incomplete pages and unrecoverable input.
- Failed recovery leaves both the source and any pre-existing destination unchanged.
- Tests include missing xref entries, damaged streams, invalid files, encrypted files and cancellation.

## DIFF-01: PDF comparison

**User experience**
- Choose two open PDFs or two files; view them side by side with synchronized page navigation and zoom.
- Highlight added, removed and altered text plus visibly changed regions.
- Navigate differences and show a per-page change summary.
- Clearly distinguish visual changes from text changes and OCR uncertainty.

**Implementation**
- Build a read-only comparison service using extracted words/bounds plus optional page-image differences.
- Compare page counts and page sizes first; normalize rendering resolution and alignment before pixel comparisons.
- Keep comparison results attached to the correct document revisions and invalidate on edits.
- Use cancellable workers for large files; do not rewrite either input.

**Acceptance**
- Detect changed words, added/removed pages and obvious visual differences.
- Identical files report no differences at the configured comparison tolerance.
- Side-by-side navigation remains usable and neither source is modified.
- Tests cover text, images, rotations, different page sizes, scanned pages and cancellation.

## REDACT-01: Permanent redaction

**User experience**
- Mark rectangular areas or search for specific text, review every match, then Apply Redactions.
- Show a clear warning that redaction permanently removes underlying content in the saved copy.
- Save a separate redacted PDF and display a verification result.

**Implementation**
- Use actual content redaction (`Page.add_redact_annot()` and `Page.apply_redactions()`), not an opaque rectangle overlay.
- Explicitly define handling for images, vector paths, annotations, form values, metadata and embedded files.
- Produce a full rewritten output without source revision history; never use incremental save for a redacted copy.
- Reopen and inspect the result for surviving targeted text, images and other recoverable copies. Fail closed if verification is incomplete.
- Require explicit consent or refuse when signed or protected documents cannot be safely rewritten.

**Acceptance**
- Redacted text cannot be found by search, copy/paste, extraction or inspecting prior incremental revisions in the output.
- Targeted areas are removed from text, OCR layers and visible imagery as appropriate.
- Incomplete verification prevents a success message.
- Tests cover underlying text, scanned images, shared resources, forms, metadata, protected/signed PDFs and repeated saves.

## TEXT-01: Advanced editing of existing PDF text

**Current state:** `TextBoxService` adds/edits FreeText annotations, but cannot edit the document's existing page text.

**User experience**
- Select a text line or supported text block and edit its actual contents.
- Adjust font, size, color and alignment where the source font/layout permits.
- Preview wrapping and overflow before applying; undo or cancel before saving.
- Explain clearly when existing text cannot be safely edited, rather than damaging the page.

**Implementation**
- Extract text spans with font, glyph, baseline and geometric information.
- Start with simple horizontal single-line text. Expand to multiline blocks only after regression coverage.
- Use a safe replacement technique with explicit checks for embedded fonts, clipping, overlaps, layout and hidden text; never silently rasterize an entire page.
- Keep user-added FreeText editing separate from edits to existing PDF content.

**Acceptance**
- Supported text edits save and reopen with the new text in the intended location.
- Unchanged neighboring text and graphics remain intact.
- Unsupported fonts, complex scripts, layouts and overlap are refused without partial edits.
- Tests cover font availability, overflow, rotated pages, multi-column layouts, undo and save/reopen.

## REPLACE-01: Find and replace in a document

**User experience**
- Find text across all pages with next/previous, case sensitivity and whole-word options.
- Replace Current or Replace All with a preview of candidate changes and page counts.
- Show skipped matches and reasons; do not claim every hit is editable.
- Search recognized OCR text, but clearly separate searching a scan from editing its image pixels.

**Implementation**
- Reuse the unified search/index service from OCR-01 and the verified edit engine from TEXT-01.
- Treat each replacement as a planned, individually validated operation, not a blind text overlay.
- Group Replace All as one undoable user action when supported; stop or roll back on partial failure.
- Never change form fields, annotations, image-only text or signatures without an explicit supported path.

**Acceptance**
- Case/whole-word options work across pages and return stable positions.
- Replace All changes only approved editable matches, preserves unrelated content and reports skips.
- Save/reopen reflects replacements; failed batches do not leave half-applied output.
- Tests cover repeated terms, Unicode, OCR-only pages, missing fonts, protected files and undo.

## SIGN-01: Certificate-based digital signatures

**Current state:** SABL supports drawn/image signature marks only. Those are not cryptographic signatures.

**User experience**
- Sign using a local PKCS#12 certificate (`.p12` or `.pfx`) and its password, with an optional visible signature appearance.
- Inspect signatures and show signer, signing time, document integrity and validation status.
- Distinguish cryptographically valid, invalid and unverified trust states. Offline trust/revocation checks may be inconclusive.
- Warn before later edits that would invalidate a signature.

**Implementation**
- Evaluate `pyHanko` as a dedicated PDF signing and validation dependency, including packaging, licensing and security review.
- Create signature fields and sign with incremental, signature-preserving updates where supported.
- Keep certificate passwords in memory for the operation only; never save private keys or passwords to application settings/logs.
- Treat certificate signature verification separately from visual signature placement.

**Acceptance**
- A locally signed PDF verifies in SABL and an independent PDF validator.
- Modifying signed bytes is reported as invalidating or altering signature coverage, as appropriate.
- Missing certificates, wrong passwords, untrusted chains and unsupported signatures yield specific statuses.
- Tests cover signing, tampering, multiple revisions, expired certificates, protected PDFs and interrupted saves.

## Shared technical checkpoints

- Establish a common output-writing helper for temporary files, overwrite confirmation, reopen validation and atomic replacement where supported. Reuse it across COMP-01, REPAIR-01, REDACT-01 and PASS-01.
- Centralize permission checks before adding more document-changing tools.
- Add small fixture PDFs for damaged objects, password permissions, scans, existing text/fonts, redaction targets and digital signatures.
- Keep implementation decisions auditable: never label a visual overlay a redaction or a drawn mark a digital signature.
- For each future feature PR, run `scripts/test.ps1` (or equivalent `python -m pytest`, `python -m compileall -q src` and `ruff check .`), and record actual results in the PR body.

## References

- [SABL architecture and workflow](AGENTS.md)
- [PyMuPDF page redactions and OCR](https://pymupdf.readthedocs.io/en/latest/page.html)
- [PyMuPDF document save and encryption](https://pymupdf.readthedocs.io/en/latest/document.html)
- [pyHanko signing and validation](https://docs.pyhanko.eu/en/latest/)
- [KillerPDF feature reference](https://github.com/SteveTheKiller/KillerPDF)
