"""
Przykladowa strategia wlasna: adaptive_profit
=============================================
Autorzy: Mikolaj Rutkowski, Stanislaw Nagorski

Strategia łączy dwa sygnały:
  1. Zajetosc bufora SUS (s) — im mniej w buforze, tym bardziej agresywny COMMIT
  2. Oczekiwany zysk netto E[pi_i] — faworyzuje fazy z lepszym stosunkiem zysk/ryzyko

Logika:
  - Bazowe P(COMMIT) = base_zeta, korygowane o odchylenie bufora od s_target
    (kazda jednostka deficytu podnosi zete o 0.04, nadwyzka ja obniza)
  - Mnoznik per faza: E[pi_i] > 0 -> mnoznik > 1 (agresywniej),
                      E[pi_i] < 0 -> mnoznik < 1 (ostrozniej)
  - Faza 5 (phi=1.0): zawsze ABSTAIN — awaria gwarantowana
  - Wynik clipowany do [0.0, 1.0]

Parametry (--param k=v):
  s_target  int   10   Pozadany poziom bufora SUS
  base_zeta float 0.7  Bazowe P(COMMIT) przy s == s_target
  scale     float 1.5  Sila wplywu zysku per faze na mnoznik

Uruchomienie:
  python sph_sim.py --custom examples/przykladowa_strategia_wlasna.py --seed 42 --json
  python sph_sim.py --custom examples/przykladowa_strategia_wlasna.py --seed 42 \\
      --param s_target=8 --param base_zeta=0.75 --param scale=2.0
  python sph_sim.py --custom examples/przykladowa_strategia_wlasna.py --seed 42 --compare-agent
  python sph_sim.py --custom examples/przykladowa_strategia_wlasna.py --batch --seeds 20 --json

Oczekiwane wyniki (seed=42, parametry domyslne):
  avg_val_last100 >= 95    (baseline naive: 92.0)
  avg_net_profit  >= 170   (baseline naive: 140.76)
"""

import random

STRATEGY_META = {
    "name": "adaptive_profit",
    "description": (
        "Hybrydowa strategia laczaca adaptacje do poziomu bufora SUS "
        "z priorytetyzacja faz o wysokim oczekiwanym zysku netto. "
        "Gdy bufor jest niski, agresywnie zwieksza P(COMMIT); "
        "fazy z wysokim ryzykiem awarii dostaja nizsze prawdopodobienstwo."
    ),
    "params": [
        ("s_target",  int,   10,  "Pozadany poziom bufora SUS"),
        ("base_zeta", float, 0.7, "Bazowe P(COMMIT) przy s == s_target"),
        ("scale",     float, 1.5, "Sila skalowania zysku per faza"),
    ],
    "baseline_kpi": {
        "avg_val_last100": 92.0,
        "avg_net_profit":  140.76,
    },
}


def strategy_adaptive_profit(dev, l, s, phi, kappa, rho, h, p, **kwargs):
    """
    Argumenty przekazywane przez symulator:
      dev   — urzadzenie: dev.phase (1..5), dev.mode ('up'/'down')
      l     — slownik {faza: liczba_dostawcow} w biezacym cyklu
      s     — biezaca zajetosc bufora SUS (int)
      phi   — lista prawdopodobienstw awarii [phi_1 .. phi_5]
      kappa — koszt dostarczenia kappa (float)
      rho   — lista kosztow naprawy [rho_1 .. rho_5]
      h     — funkcja h(i) = i^alpha (callable)
      p     — platnosci per faza: dict {faza: wartosc} lub float

    Zwraca: 'commit' lub 'abstain'
    """
    # --- Odczyt parametrow ---
    s_target  = int(kwargs.get("s_target",  10))
    base_zeta = float(kwargs.get("base_zeta", 0.7))
    scale     = float(kwargs.get("scale",     1.5))

    i = dev.phase  # aktualna faza urzadzenia (1..5)

    # Faza 5: phi=1.0 -> awaria gwarantowana -> zawsze ABSTAIN
    if i >= 5:
        return "abstain"

    # --- Wyodrebnij platnosc dla biezacej fazy ---
    if isinstance(p, dict):
        p_i = float(p.get(i, 0.0))
    else:
        p_i = float(p)

    # --- Sygnal 1: adaptacja do bufora SUS ---
    # deficit > 0  => bufor niski  => podnosimy zete
    # deficit < 0  => bufor pelny  => obnizamy zete
    deficit  = s_target - s
    zeta_buf = base_zeta + 0.04 * deficit
    zeta_buf = max(0.0, min(1.0, zeta_buf))

    # --- Sygnal 2: mnoznik oparty na E[pi_i | commit] ---
    # E[pi_i] = (1 - phi_i) * p_i - kappa - phi_i * rho_i
    phi_i = phi[i - 1]
    rho_i = rho[i - 1]
    expected_profit = (1.0 - phi_i) * p_i - kappa - phi_i * rho_i

    if expected_profit > 0:
        profit_multiplier = 1.0 + scale * (expected_profit / (abs(expected_profit) + 1.0))
    else:
        profit_multiplier = max(0.1, 1.0 + scale * (expected_profit / (abs(expected_profit) + 1.0)))

    # --- Laczne P(COMMIT) ---
    zeta_final = zeta_buf * profit_multiplier
    zeta_final = max(0.0, min(1.0, zeta_final))

    return "commit" if random.random() < zeta_final else "abstain"
