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


def parse_args():
    p = argparse.ArgumentParser(
        description='SPH Symulator — testuj strategię rekomendacji COMMIT/ABSTAIN',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    mutex = p.add_mutually_exclusive_group(required=True)
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
    # Post-parse mutex checks (D-60) — twarde błędy z polskim komunikatem.
    if args.compare_agent and args.no_agent:
        p.error("Flagi --compare-agent i --no-agent są wzajemnie wykluczające.")
    if args.compare_agent and args.interactive:
        p.error("Flaga --compare-agent nie działa w trybie --interactive.")
    return args
