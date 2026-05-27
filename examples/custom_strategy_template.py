"""Szablon custom strategii dla SPH Symulatora (Phase 3).

Skopiuj ten plik gdziekolwiek (np. ~/moje-strategie/my_strat.py),
zmień nazwę pliku i nazwę funkcji na strategy_<nowy_basename>, uruchom przez:

    python sph_sim.py --custom <ścieżka>.py --param max_phase=3 --seed 42

Reguła nazewnictwa (D-34 + D-35): nazwa funkcji MUSI być
`strategy_<basename_pliku_bez_py>` — np. dla `my_strat.py` → `strategy_my_strat`.

Uwaga bezpieczeństwa: loader wykonuje ten plik jak każdy moduł Pythona
(projekt akademicki, lokalny — bez sandboxa). Banner [OSTRZEŻENIE]
przypomina o tym przed każdym ładowaniem.
"""

# Argumenty funkcji strategii (DOKŁADNIE w tej kolejności, nazwy jak w sygnaturze):
#   dev    — bieżące urządzenie (obiekt Device z polami: id, phase 1..F-1, status 'UP'/'DOWN')
#   l      — list[int] — liczba dostawców per faza z POPRZEDNIEGO cyklu, długość F-1
#   s      — int — bieżąca zajętość bufora SUS (0..nSUS)
#   phi    — list[float] — P(awarii) per faza, długość F
#   kappa  — float — koszt commit (dostarczenia usługi)
#   rho    — list[float] — koszt awarii per faza, długość F
#   h      — callable(int) -> float — funkcja wagi i^alpha
#   p      — dict — params strategii (z --param k=v lub k=v w REPL)
#
# Wartość zwrotna: literal string 'COMMIT' albo 'ABSTAIN' (NIE enum, NIE bool).


def strategy_custom_strategy_template(dev, l, s, phi, kappa, rho, h, p):
    # Guard: tylko urządzenia UP podejmują decyzję (DOWN są w cyklu naprawy)
    if dev.status != 'UP':
        return 'ABSTAIN'

    # Czytamy parametr 'max_phase' — przekazany przez --param max_phase=N lub default 4
    max_phase = int(p.get('max_phase', 4))

    # Prosta reguła: COMMIT dla wczesnych faz, ABSTAIN dla późnych
    # (alias `threshold` z innym defaultem — pokazuje jak iść własną drogą)
    return 'COMMIT' if dev.phase <= max_phase else 'ABSTAIN'


# Metadane strategii — wymagany kontrakt (loader D-47 layer 4)
# Klucze: 'description' (str), 'params' (list[tuple-4]), 'baseline_kpi' (dict|None)
STRATEGY_META = {
    'description': 'Szablon: COMMIT dla faz <= max_phase (przykład dydaktyczny)',
    'params': [
        # (nazwa, typ_callable, wartość_domyślna, opis_polski)
        ('max_phase', int, 4, 'Maksymalna faza dla COMMIT'),
    ],
    'baseline_kpi': None,  # opcjonalne — gdy znasz baseline, podaj dict z 'invocation' i 'avg_val_last100'
}
