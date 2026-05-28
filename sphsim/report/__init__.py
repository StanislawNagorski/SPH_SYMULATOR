"""Generator raportu MD + wykresów PNG (Phase 6, REPORT-01..03, PLOT-01..03).

Public surface:
  - render_report(args, res, params, K1, *, mode='single'|'compare') -> str
    Pure function — returns full Markdown report as single string.

  - write_report(args, res, params, K1, *, mode='single'|'compare') -> Path | None
    ORCHESTRATOR — inserted by Plan 04 (Wave 3). Creates ./reports/<ts>/,
    calls render_report + plot_* functions, writes 3 files. Returns Path
    to created dir or None when opt-out (SPHSIM_NO_REPORT=1) or mkdir fail.

Plan 02 (Wave 2) lands the pure-function side (render_report + markdown
assembly). Plan 03 (Wave 2 parallel) lands the plot generators. Plan 04
(Wave 3) wires them together via write_report.
"""
from sphsim.report.markdown import render_report

# Plan 04 placeholder — write_report orchestrator inserted here in Wave 3.
# Do not modify this file in Plan 03 (plotting side stays in plots.py).

__all__ = ['render_report']
