# docs/report/

`Shadow_Agent_Pro_Report.docx` is a complete starting draft covering the
structure originally scoped for this project: Certificate, Acknowledgement,
Abstract, Chapter 1 (Introduction), Chapter 2 (Literature Review), Chapter 3
(Materials & Methods), Chapter 4 (Results & Discussion), and an Appendix.

## This is a real draft, not a template with placeholders

Every section contains actual content specific to this project — real
architecture decisions, real training results (87% RF / 92% char n-gram
accuracy on the real dataset), and a genuine documented finding (the
brand-name allowlist bug and fix, described in Chapter 4.2) rather than
generic filler text. You should still read through it, adjust names/dates/
supervisor details if anything has changed, and update the results tables
if you retrain with different data or parameters than what's described.

## Things you'll likely want to do in Word before submitting

- **Insert a Table of Contents**: References → Table of Contents. All
  chapter/section headings use Word's built-in heading styles, so this
  is a one-click operation — it wasn't auto-generated here since a TOC
  field needs Word itself to compute page numbers correctly.
- **Add page numbers**: Insert → Page Number.
- **Update the results tables** in Chapter 4.1 if you retrain with a
  different sample size or dataset than the 3,000-per-class real-data run
  described here — re-run `train.py` and copy its printed evaluation
  metrics in.
- **Add screenshots** of the dashboard/extension if your course requires
  visual evidence of a working system — the Overview, Threats, and Live
  Ops dashboard tabs make good candidates.
- **Cross-check enrollment numbers, supervisor, and HOD names** against
  your actual current records before submission.

## Regenerating the report

The report was generated programmatically (not written directly in
Word) so it could be verified end-to-end — rendered to PDF and visually
inspected before being included in this project — and so it can be
regenerated if you want to script further changes rather than editing
the `.docx` by hand. If you want the generation script, ask — it wasn't
included in this folder since the finished `.docx` is what you actually
need for submission.
