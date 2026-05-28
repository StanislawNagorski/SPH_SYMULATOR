"""Generator raportu MD + wykresów PNG (Phase 6, REPORT-01..03, PLOT-01..03).

Public surface:
  - write_report(args, res, params, K1, *, mode='single'|'compare',
                 report_dir_override=None) -> Path | None
    Orchestrator — tworzy ./reports/<ts>/ (lub `report_dir_override` jeśli podany
    przez tutorial caller — D-10, plan 08-01), woła render_report + plot_*,
    zapisuje 3 pliki. Zwraca Path do katalogu raportu lub None gdy:
      (a) opt-out env var SPHSIM_NO_REPORT=1 ustawione (sprawdzane PRZED override —
          Pitfall 4),
      (b) mkdir failure (PermissionError, OSError) — tylko w default branch
          (override używa exist_ok=True, więc kolizja nie wywala),
      (c) render_report rzucił wyjątek.
    Nigdy nie rzuca — wszystkie wyjątki łapane i logowane na stderr
    (RESEARCH §C.7 + Pitfall 6 — report side-effect MUST NOT crash CLI).

  - write_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list, *,
                       report_dir_override=None) -> Path | None
    Symetryczne do write_report, dla batch mode. Identyczna semantyka override.

  - render_report(args, res, params, K1, *, mode) -> str
    Re-eksport z markdown.py — pure function, używana też przez testy.

Opt-out: env var SPHSIM_NO_REPORT=1 (CI, regression check, tests). Caller
otrzymuje None — pozwala pominąć banner i kontynuować bez side-effectów.

Banner: 'Raport zapisany do: ...' zawsze drukowany przez CALLER (main.py /
repl.py) na sys.stderr (Pitfall 3 — stdout cleanliness dla --json mode).
write_report samo zwraca Path; banner jest decyzją wywołującego, NIE
write_report.

D-10 (plan 08-01): `report_dir_override` to opcjonalny kwarg keyword-only
używany przez tutorial mode (plan 08-04) — pozwala kierować raport do
`./reports/tutorial-<ts>/step-N-<topic>/` zamiast domyślnego `./reports/<ts>/`.
Default (None) zachowuje byte-identyczne zachowanie z v1.1.7 (regression_check
PASS=8/8 invariant). Override branch używa `mkdir(parents=True, exist_ok=True)`
— tutorial caller może retry'ować ten sam step bez kolizji.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

from sphsim.report.markdown import render_report
from sphsim.report.plots import plot_decision_distribution, plot_kpi_timeseries

__all__ = ['write_report', 'render_report', 'write_batch_report']


def _timestamp() -> str:
    """ISO-like, fs-safe na Windows: %Y%m%d-%H%M%S (RESEARCH §C.7)."""
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def _resolve_report_dir(base: Path = None) -> Path:
    """Tworzy ./reports/<ts>/ z collision retry suffiks -N (RESEARCH §C.7).

    Args:
        base: opcjonalny base directory (test override); default Path('reports').

    Returns:
        Path do utworzonego katalogu (mkdir wykonany).

    Raises:
        OSError (PermissionError, etc.) — handled by caller; NIE propaguje do CLI.
    """
    base = base if base is not None else Path('reports')
    ts = _timestamp()
    candidate = base / ts
    n = 1
    while candidate.exists():
        n += 1
        candidate = base / f'{ts}-{n}'
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def _extract_plot_source(res, mode):
    """Wybiera dict z danymi dla PNG-ów: w compare bierze _with_agent_full (z history).

    Plot generators (plot_decision_distribution, plot_kpi_timeseries) potrzebują
    history list — która jest strippowana z comparison.with_agent dict-comp.
    Resolution (RESEARCH §N.1): run_compare wstrzykuje '_with_agent_full' (full
    res_with z history) jako prywatny klucz; write_report konsumuje, format_json
    strippuje underscore-prefixed top-level keys.
    """
    if mode == 'compare':
        # Preferowane: _with_agent_full key (RESEARCH §N.1 resolution — full res_with).
        # Fallback: comparison.with_agent (bez history — plot_kpi_timeseries silent-skipuje).
        return res.get('_with_agent_full') or res.get('comparison', {}).get('with_agent', {})
    return res


def write_report(args, res, params, K1, *, mode='single', report_dir_override=None):
    """Zapisuje raport MD + 2 PNG do ./reports/<timestamp>/ (lub override path).

    Args:
        args:                argparse.Namespace (CLI args lub fake_args z REPL).
        res:                 dict z sim.run() (single) lub run_compare (compare).
        params:              dict parametrów strategii.
        K1:                  float (może być float('inf')).
        mode:                'single' | 'compare' (keyword-only).
        report_dir_override: opcjonalny Path (D-10, plan 08-01). Gdy podany,
                             raport jest zapisany dokładnie do tej ścieżki
                             (z mkdir(parents=True, exist_ok=True)) — bypass
                             default'owego `./reports/<ts>/`. Używane przez
                             tutorial mode (plan 08-04). Default None
                             zachowuje byte-identyczne zachowanie v1.1.7.

    Returns:
        pathlib.Path do utworzonego katalogu, lub None gdy raport pominięty
        (opt-out env var SPHSIM_NO_REPORT=1 lub mkdir/render failure).

    Side effects:
        mkdir ./reports/<ts>/ (lub override path) + zapis 3 plików
        (report.md + 2 PNG). Wszystkie wyjątki łapane — write_report nigdy nie
        rzuca do CLI. Banner 'Raport zapisany do: ...' emitowany przez CALLER
        (na sys.stderr).
    """
    # ── Opt-out (Pitfall 4) — MUSI zostać PRZED override logic ──
    # SPHSIM_NO_REPORT=1 wygrywa nad każdym override (CI/regression-check invariant).
    if os.environ.get('SPHSIM_NO_REPORT') == '1':
        return None

    # ── Exception isolation (Pitfall 6 — RESEARCH §C.7) ──
    # Całe ciało otoczone try/except — report side-effect MUST NOT crash CLI.
    try:
        # ── D-10 (plan 08-01): override branch dla tutorial mode ──
        # exist_ok=True — tutorial caller może wielokrotnie wywołać dla tego
        # samego stepa (np. hint retry). Default branch zachowuje exist_ok=False
        # przez _resolve_report_dir collision-retry suffix.
        if report_dir_override is not None:
            report_dir = Path(report_dir_override)
            report_dir.mkdir(parents=True, exist_ok=True)
        else:
            try:
                report_dir = _resolve_report_dir()
            except OSError as e:
                print(f'[OSTRZEŻENIE] Nie udało się utworzyć katalogu raportu: {e}. '
                      f'Raport pominięty.', file=sys.stderr)
                return None

        plot_res = _extract_plot_source(res, mode)

        # Plot generation — defensive: catch ALL exceptions so report.md still writes
        # nawet jeśli matplotlib z jakiegoś powodu się wywali (font issue, OOM, ...).
        try:
            plot_decision_distribution(
                plot_res.get('ic_per_phase', {}),
                plot_res.get('veto_per_phase', {}),
                plot_res.get('abstain_per_phase', {}),
                report_dir / 'decision_distribution.png',
            )
        except Exception as e:
            print(f'[OSTRZEŻENIE] Błąd generowania decision_distribution.png: {e}. '
                  f'Kontynuuję.', file=sys.stderr)
        try:
            plot_kpi_timeseries(
                plot_res.get('history', {}),
                args.T,
                report_dir / 'kpi_timeseries.png',
            )
        except Exception as e:
            print(f'[OSTRZEŻENIE] Błąd generowania kpi_timeseries.png: {e}. '
                  f'Kontynuuję.', file=sys.stderr)

        # Markdown — jeśli się nie zapisze, raport jest bezużyteczny; zwracamy None
        # żeby caller NIE wypisał false-positive banner.
        try:
            md = render_report(args, res, params, K1, mode=mode)
            (report_dir / 'report.md').write_text(md, encoding='utf-8')
        except Exception as e:
            print(f'[OSTRZEŻENIE] Błąd generowania raportu MD: {e}. '
                  f'Raport niekompletny.', file=sys.stderr)
            return None

        return report_dir

    except Exception as e:
        # Last-resort catch — gdyby coś przeciekło (np. nieoczekiwany TypeError
        # przy formatowaniu komunikatu wyżej). Nigdy nie pozwalamy report side-
        # effect zabić CLI.
        print(f'[OSTRZEŻENIE] Raport: {e}', file=sys.stderr)
        return None


def write_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list):
    """Phase 7 BATCH-03+PLOT-04: zapisuje raport batchowy MD + boxplot PNG.

    Symetryczne API do `write_report`, ale konsumuje LISTĘ dictów (jeden per seed) +
    aggregate (z `aggregate_kpis`) zamiast pojedynczego `res`. Tworzy katalog
    `./reports/batch_<timestamp>/` z dwoma plikami: `report.md` + `batch_aggregate.png`.

    Args:
        args:             argparse.Namespace (wymagane pola: nU, nSUS, T, kappa,
                          alpha, K0, phi, rho, seed, strategy, no_agent).
        per_seed_results: list[dict[str, float]] — N dictów z 5 kluczami z KPIS,
                          jeden per seed (output `run_batch`).
        aggregate:        dict[str, AggregateStat] — `aggregate_kpis` output.
        params:           dict parametrów strategii.
        K1:               float (może być float('inf')).
        seeds_list:       list[int] — wartości seedów odpowiadające per_seed_results.

    Returns:
        pathlib.Path do utworzonego katalogu, lub None gdy:
          (a) opt-out env var SPHSIM_NO_REPORT=1 ustawione,
          (b) mkdir failure,
          (c) render_batch_report rzucił wyjątek.

    Side effects:
        mkdir `./reports/batch_<ts>/` + zapis 2 plików (report.md + batch_aggregate.png).
        Wszystkie wyjątki łapane — write_batch_report NIGDY nie rzuca do CLI.
        Banner 'Raport batchowy zapisany do: ...' emitowany przez CALLER (na sys.stderr).
    """
    # ── Opt-out (Phase 6 contract preserved) ──
    if os.environ.get('SPHSIM_NO_REPORT') == '1':
        return None

    # ── Exception isolation (Pitfall 6) — raport NIGDY nie zabija CLI ──
    try:
        # mkdir with collision retry (-N suffix) — symmetric to _resolve_report_dir.
        try:
            ts = _timestamp()
            base = Path('reports') / f'batch_{ts}'
            n = 1
            while base.exists():
                n += 1
                base = Path('reports') / f'batch_{ts}-{n}'
            base.mkdir(parents=True, exist_ok=False)
            report_dir = base
        except OSError as e:
            print(f'[OSTRZEŻENIE] Nie udało się utworzyć katalogu raportu batch: {e}. '
                  f'Raport pominięty.', file=sys.stderr)
            return None

        # Plot generation — defensive: catch ALL exceptions so MD still writes
        # nawet jeśli matplotlib z jakiegoś powodu się wywali (font issue, OOM, ...).
        try:
            from sphsim.report.plots import plot_batch_aggregate
            plot_batch_aggregate(per_seed_results, report_dir / 'batch_aggregate.png')
        except Exception as e:
            print(f'[OSTRZEŻENIE] Błąd generowania batch_aggregate.png: {e}. '
                  f'Kontynuuję.', file=sys.stderr)

        # Markdown — jeśli się nie zapisze, raport jest bezużyteczny; zwracamy None
        # żeby caller NIE wypisał false-positive banner.
        try:
            from sphsim.report.batch_markdown import render_batch_report
            md = render_batch_report(args, per_seed_results, aggregate, params, K1, seeds_list)
            (report_dir / 'report.md').write_text(md, encoding='utf-8')
        except Exception as e:
            print(f'[OSTRZEŻENIE] Błąd generowania raportu batch MD: {e}. '
                  f'Raport niekompletny.', file=sys.stderr)
            return None

        return report_dir

    except Exception as e:
        # Last-resort catch — nigdy nie pozwalamy report side-effect zabić CLI.
        print(f'[OSTRZEŻENIE] Raport batch: {e}', file=sys.stderr)
        return None
