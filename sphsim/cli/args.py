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
from sphsim.strategies import STRATEGIES
from sphsim.config import DEFAULT_NU, DEFAULT_NSUS, DEFAULT_K1, DEFAULT_T, DEFAULT_KAPPA, DEFAULT_ALPHA


def parse_args():
    p = argparse.ArgumentParser(
        description='SPH Symulator — testuj strategię rekomendacji COMMIT/ABSTAIN',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    mutex = p.add_mutually_exclusive_group(required=True)
    mutex.add_argument('--interactive', action='store_true',
                       help='Uruchom tryb interaktywny (REPL)')
    mutex.add_argument('--strategy', choices=list(STRATEGIES.keys()),
                       help='Strategia: ' + ', '.join(STRATEGIES.keys()))
    # Parametry strategii
    p.add_argument('--zeta',       type=float, default=0.5,   help='[naive] Frakcja COMMIT (0..1)')
    p.add_argument('--max_phase',  type=int,   default=3,     help='[threshold] Max faza COMMIT')
    p.add_argument('--probs',      type=str,   default='0.9,0.7,0.5,0.3,0.0',
                   help='[phase_prob] P(COMMIT) per faza, po przecinku')
    p.add_argument('--s_target',   type=int,   default=10,    help='[adaptive] Próg SUS')
    p.add_argument('--expected_P', type=float, default=100.0, help='[incentive] Oczek. płatność')
    # Parametry środowiska
    p.add_argument('--nU',   type=int,   default=DEFAULT_NU,    help=f'Liczba urządzeń (def {DEFAULT_NU})')
    p.add_argument('--nSUS', type=int,   default=DEFAULT_NSUS,  help=f'Pojemność SUS (def {DEFAULT_NSUS})')
    p.add_argument('--K1',   type=float, default=DEFAULT_K1,    help=f'Górna granica waluacji (def {DEFAULT_K1})')
    p.add_argument('--T',    type=int,   default=DEFAULT_T,     help=f'Liczba cykli (def {DEFAULT_T})')
    p.add_argument('--kappa',type=float, default=DEFAULT_KAPPA, help=f'Koszt dostarczenia (def {DEFAULT_KAPPA})')
    p.add_argument('--alpha',type=float, default=DEFAULT_ALPHA, help=f'Wykładnik h(i)=i^alpha (def {DEFAULT_ALPHA})')
    p.add_argument('--seed', type=int,   default=42,            help='Ziarno losowe (def 42)')
    p.add_argument('--json', action='store_true', help='Wynik jako JSON (do parsowania)')
    p.add_argument('--verbose', action='store_true', help='Szczegółowe logi co 100 cykli')
    return p.parse_args()
