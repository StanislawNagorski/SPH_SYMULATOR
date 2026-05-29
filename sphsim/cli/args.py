"""
=============================================================
  MEDIACJA TRANSFERU PŁATNYCH USŁUG — Symulator Strategii
  Autorzy: Stanisław Nagórski, Mikołaj Rutkowski
  Na podstawie: J. Konorski, MPE cz. 2, Katedra Teleinformatyki WETI
=============================================================

UŻYCIE (jedna linia):
  python sph_sim.py --strategy <NAZWA> [parametry_strategii] [parametry_srodowiska]

PRZYKŁADY:
  python sph_sim.py --strategy naive --zeta 0.5
  python sph_sim.py --strategy threshold --max_phase 3
  python sph_sim.py --strategy phase_prob --probs 0.9,0.7,0.5,0.3,0.0
  python sph_sim.py --strategy incentive --expected_P 100
  python sph_sim.py --strategy adaptive --s_target 10
  python sph_sim.py --strategy naive --zeta 0.4 --nU 200 --nSUS 20 --K1 120 --T 1000
  python sph_sim.py --strategy phase_prob --probs 1.0,0.8,0.6,0.2,0.0 --kappa 0.5 --alpha 0 --json

DOSTĘPNE STRATEGIE:
  naive       -- COMMIT dla zeta*100% urządzeń w każdej fazie
  threshold   -- COMMIT tylko dla faz <= max_phase
  phase_prob  -- COMMIT z prawdopodobieństwem per faza (lista probs)
  incentive   -- COMMIT gdy E[zysk_netto] > 0 (zgodna motywacyjnie)
  adaptive    -- COMMIT zależnie od poziomu bufora SUS
"""
import argparse
import sys
from sphsim.strategies import STRATEGIES, BUILTIN_STRATEGIES
from sphsim.config import DEFAULT_NU, DEFAULT_NSUS, DEFAULT_K0, DEFAULT_K1, DEFAULT_T, DEFAULT_KAPPA, DEFAULT_ALPHA, DEFAULT_PHI, DEFAULT_RHO


def _parse_phi_list(s: str) -> list:
    """Konwertuje string 'p1,p2,p3,p4,p5' na listę 5 floatów ∈ [0,1] (ENV-01, D-17)."""
    try:
        vals = [float(x.strip()) for x in s.split(',')]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Nieprawidłowy format --phi: '{s}'. Oczekiwano 5 liczb po przecinku, np. 0.1,0.2,0.3,0.4,1.0"
        )
    if len(vals) != 5:
        raise argparse.ArgumentTypeError(
            f"--phi wymaga dokładnie 5 wartości (podano {len(vals)}): '{s}'"
        )
    for i, v in enumerate(vals):
        if not (0.0 <= v <= 1.0):
            raise argparse.ArgumentTypeError(
                f"--phi[{i+1}]={v} poza zakresem [0, 1]. Wszystkie wartości φ muszą być w [0, 1]."
            )
    return vals


def _parse_rho_list(s: str) -> list:
    """Konwertuje string 'r1,r2,r3,r4,r5' na listę 5 floatów ≥ 0 (ENV-01, D-17)."""
    try:
        vals = [float(x.strip()) for x in s.split(',')]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Nieprawidłowy format --rho: '{s}'. Oczekiwano 5 liczb po przecinku, np. 0.5,0.5,0.7,1.5,3.0"
        )
    if len(vals) != 5:
        raise argparse.ArgumentTypeError(
            f"--rho wymaga dokładnie 5 wartości (podano {len(vals)}): '{s}'"
        )
    for i, v in enumerate(vals):
        if v < 0.0:
            raise argparse.ArgumentTypeError(
                f"--rho[{i+1}]={v} jest ujemne. Wszystkie wartości ρ muszą być ≥ 0."
            )
    return vals


# Phase 7 — DoS prevention cap (T-7-02-01). Applied to BOTH grammar branches:
# single-N (--seeds N → range(1, N+1)) AND comma-list (post-dedup length check).
# 1000 seeds × ~150ms ≈ 150s — generous upper bound for legitimate research
# while preventing accidental OOM from a typo like '--seeds 9999999'.
MAX_SEEDS = 1000


def _parse_seeds_list(s: str) -> list:
    """Konwertuje '--seeds N' (1..N) lub '--seeds n1,n2,...' (jawna lista) na list[int] (BATCH-01).

    Grammar (RESEARCH §B.3, lock v1):
        '10'           → [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]   (single positive int → range)
        '1,5,42,100'   → [1, 5, 42, 100]                   (comma list, preserve order)
        '1,1,2,1'      → [1, 2]                            (dedup, preserve first occurrence)
        '42'           → [42]                              (single int = list of one)
        '0', '-5'      → ArgumentTypeError                 (reject — must be positive)
        '', 'abc'      → ArgumentTypeError                 (reject — empty / non-numeric)
        '1.5'          → ArgumentTypeError                 (reject — int() fails on float-string)
        '1..10'        → ArgumentTypeError                 (reject — range syntax is v2 feature)
        '1001'+        → ArgumentTypeError                 (reject — DoS cap MAX_SEEDS=1000)

    Used by argparse `type=` on `--seeds` and reused by REPL command parser (Plan 07-05).
    """
    s = s.strip()
    if not s:
        raise argparse.ArgumentTypeError(
            "Pusta wartość --seeds. Podaj N (np. --seeds 10) lub listę (np. --seeds 1,5,42).")
    if ',' in s:
        try:
            raw = [int(x.strip()) for x in s.split(',')]
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Nieprawidłowy format --seeds: '{s}'. Oczekiwano listy integerów (np. 1,5,42).")
        if any(v <= 0 for v in raw):
            raise argparse.ArgumentTypeError(
                f"--seeds: wszystkie wartości muszą być dodatnie (> 0); podano: {raw}.")
        seen = set()
        result = []
        for v in raw:
            if v not in seen:
                seen.add(v)
                result.append(v)
        if len(result) > MAX_SEEDS:
            raise argparse.ArgumentTypeError(
                f"--seeds: lista ma {len(result)} elementów (po deduplikacji), limit {MAX_SEEDS}.")
        return result
    else:
        try:
            n = int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Nieprawidłowy format --seeds: '{s}'. "
                "Oczekiwano N (np. --seeds 10) lub listy (np. --seeds 1,5,42).")
        if n <= 0:
            raise argparse.ArgumentTypeError(
                f"--seeds: N musi być dodatnie (> 0); podano: {n}.")
        if n > MAX_SEEDS:
            raise argparse.ArgumentTypeError(
                f"--seeds: N={n} przekracza limit {MAX_SEEDS} (zapobieganie OOM). "
                f"Dla większych eksperymentów uruchom kilka mniejszych batchy.")
        return list(range(1, n + 1))


def parse_args():
    p = argparse.ArgumentParser(
        description='SPH Symulator — testuj strategię rekomendacji COMMIT/ABSTAIN',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    # Phase 8 (Plan 08-02 + UAT Gap 5 closure 08-10): required=False —
    # `--tutorial` is intentionally outside this group (analog do `--batch`)
    # and argparse enforces required=True BEFORE post-parse code runs.
    # Post-parse: if NO mode flag is set, auto-promote to --interactive +
    # print informational banner to stderr listing the 4 alternate modes.
    # This replaces the earlier Plan 08-02 hard-error contract (exit 2).
    mutex = p.add_mutually_exclusive_group(required=False)
    mutex.add_argument('--interactive', action='store_true',
                       help='Uruchom tryb interaktywny (REPL)')
    mutex.add_argument('--strategy', choices=list(BUILTIN_STRATEGIES),
                       help='Strategia: ' + ', '.join(sorted(BUILTIN_STRATEGIES)))
    mutex.add_argument('--custom',   type=str, default=None,
                       help='Ścieżka do pliku .py z custom strategią')
    # Parametry strategii
    p.add_argument('--zeta',       type=float, default=0.5,   help='[naive] Frakcja COMMIT (0..1)')
    p.add_argument('--max_phase',  type=int,   default=3,     help='[threshold] Max faza COMMIT')
    p.add_argument('--probs',      type=str,   default='0.9,0.7,0.5,0.3,0.0',
                   help='[phase_prob] P(COMMIT) per faza, po przecinku')
    p.add_argument('--s_target',   type=int,   default=10,    help='[adaptive] Próg SUS')
    p.add_argument('--expected_P', type=float, default=100.0,
                   help='[incentive|agent] Oczek. płatność (def 100.0)')
    # Param custom strategii (poza mutex; D-39, repeatable, działa tylko z --custom)
    p.add_argument('--param', action='append', dest='param', default=[], metavar='K=V',
                   help='[--custom] Parametr custom strategii, np. --param zeta=0.7 (repeatable)')
    # Parametry środowiska
    p.add_argument('--nU',   type=int,   default=DEFAULT_NU,    help=f'Liczba urządzeń (def {DEFAULT_NU})')
    p.add_argument('--nSUS', type=int,   default=DEFAULT_NSUS,  help=f'Pojemność SUS (def {DEFAULT_NSUS})')
    p.add_argument('--K1',   type=float, default=DEFAULT_K1,    help=f'Górna granica waluacji (def {DEFAULT_K1})')
    p.add_argument('--K0',   type=float, default=DEFAULT_K0,    help=f'Dolny próg waluacji K0 (def {DEFAULT_K0})')
    p.add_argument('--phi',  type=_parse_phi_list, default=DEFAULT_PHI,
                   metavar='p1,..,p5',
                   help='Profile awarii φ (5 liczb w [0,1], def: 0.1,0.2,0.3,0.4,1.0)')
    p.add_argument('--rho',  type=_parse_rho_list, default=DEFAULT_RHO,
                   metavar='r1,..,r5',
                   help='Koszty naprawy ρ (5 liczb ≥ 0, def: 0.5,0.5,0.7,1.5,3.0)')
    # Phase 7 BATCH-01 + Phase 8 (Plan 08-02) TUT-05:
    # --batch, --seeds, --tutorial — INTENTIONALLY free-standing (NOT in any
    # add_mutually_exclusive_group) so the post-parse Polish p.error fires
    # BEFORE argparse's English fallback (Warning #8 mitigation).
    p.add_argument('--batch', action='store_true',
                   help='Tryb batch — uruchom strategię N razy na różnych seedach (wymaga --seeds)')
    p.add_argument('--seeds', type=_parse_seeds_list, default=None, metavar='N|lista',
                   help='Lista seedów: N (1..N) lub jawna (1,5,42). Działa tylko z --batch.')
    p.add_argument('--tutorial', action='store_true',
                   help='Uruchom interaktywny tutorial v1.1 (≤15 min)')
    p.add_argument('--valuation', choices=['window', 'step', 'linear'], default='window',
                   help='Preset funkcji waluacji g(u): window (v1.0 default) | step | linear')
    p.add_argument('--T',    type=int,   default=DEFAULT_T,     help=f'Liczba cykli (def {DEFAULT_T})')
    p.add_argument('--kappa',type=float, default=DEFAULT_KAPPA, help=f'Koszt dostarczenia (def {DEFAULT_KAPPA})')
    p.add_argument('--alpha',type=float, default=DEFAULT_ALPHA, help=f'Wykładnik h(i)=i^alpha (def {DEFAULT_ALPHA})')
    p.add_argument('--seed', type=int,   default=42,            help='Ziarno losowe (def 42)')
    p.add_argument('--json', action='store_true', help='Wynik jako JSON (do parsowania)')
    p.add_argument('--verbose', action='store_true', help='Szczegółowe logi co 100 cykli')
    p.add_argument('--no-agent', action='store_true',
                   help='Wyłącz RationalAgent (surowa strategia, bez veto)')
    p.add_argument('--compare-agent', action='store_true',
                   help='Uruchom 2x: z agentem i bez — tabela delta KPI')
    args = p.parse_args()
    # Phase 8 (Plan 08-02) — Polish required-mode check (replaces argparse English
    # fallback po obniżeniu mutex group do required=False; --tutorial jest
    # dopuszczalnym alternatywnym trybem poza mutex group).
    if not (args.interactive or args.strategy or args.custom or args.batch or args.tutorial):
        # UAT Gap 5 (Plan 08-10): auto-promote to --interactive + print
        # Polish informational banner to stderr listing the 4 alternate
        # modes. Replaces Plan 08-02 hard-error contract — user requested
        # discoverability over penalty.
        args.interactive = True
        print("Nie podano trybu — uruchamiam tryb interaktywny (REPL).", file=sys.stderr)
        print("Dostępne tryby:", file=sys.stderr)
        print("  --interactive   Tryb REPL z komendami: strategies, run, compare, batch, tutorial.", file=sys.stderr)
        print("  --strategy NAZWA  Pojedyncza symulacja wbudowanej strategii (np. naive, incentive).", file=sys.stderr)
        print("  --custom PLIK.py  Załaduj i uruchom własną strategię z pliku .py.", file=sys.stderr)
        print("  --batch --seeds N  Uruchom strategię na wielu seedach z agregatem statystycznym.", file=sys.stderr)
        print("  --tutorial      Interaktywny tutorial v1.1 (~9 kroków, ≤15 min).", file=sys.stderr)
    # Post-parse mutex checks (D-60) — twarde błędy z polskim komunikatem.
    if args.compare_agent and args.no_agent:
        p.error("Flagi --compare-agent i --no-agent są wzajemnie wykluczające.")
    if args.compare_agent and args.interactive:
        p.error("Flaga --compare-agent nie działa w trybie --interactive.")
    # Phase 7 mutex: post-parse p.error → Polish message fires before any top-level
    # argparse English fallback (Warning #8 mitigation). --batch is NOT in any
    # add_mutually_exclusive_group, so these four Polish checks always run.
    if args.batch and args.compare_agent:
        p.error("Flagi --batch i --compare-agent są wzajemnie wykluczające.")
    if args.batch and args.interactive:
        p.error("Flaga --batch nie działa w trybie --interactive (użyj komendy `batch` w REPL).")
    # Phase 8 (Plan 08-02) TUT-05 — 5-way tutorial mutex (verbatim per PATTERNS.md).
    if args.tutorial and args.interactive:
        p.error("Flagi --tutorial i --interactive są wzajemnie wykluczające.")
    if args.tutorial and getattr(args, 'strategy', None):
        p.error("Flaga --tutorial nie działa z --strategy (użyj trybu tutorial interaktywnie).")
    if args.tutorial and args.custom:
        p.error("Flaga --tutorial nie działa z --custom.")
    if args.tutorial and args.batch:
        p.error("Flagi --tutorial i --batch są wzajemnie wykluczające.")
    if args.tutorial and args.compare_agent:
        p.error("Flagi --tutorial i --compare-agent są wzajemnie wykluczające.")
    if args.batch and args.seeds is None:
        p.error("Flaga --batch wymaga --seeds N lub --seeds lista (np. 1,5,42).")
    if args.seeds is not None and not args.batch:
        p.error("Flaga --seeds wymaga --batch.")
    return args
