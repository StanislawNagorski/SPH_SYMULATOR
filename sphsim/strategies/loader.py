"""Loader custom strategii — ładuje plik .py użytkownika przez importlib (Phase 3).

Eksportuje:
  - load_custom(path) -> (basename, fn, meta)  — pure function (rejestrację robi wywołujący, D-46)
  - parse_params_from_meta(tokens, meta, name) -> dict  — typed conversion z STRATEGY_META
  - LoaderError                                 — exception, polski komunikat w args[0]
  - EXPECTED_PARAMS                             — krotka 8 nazw sygnatury strategii

Mechanika ładowania (D-38, RESEARCH Pitfall #1):
  Loader NIGDY nie używa stdlib reload() z importlib — dla modułów
  zarejestrowanych pod syntetycznym dotted path `sphsim.custom.<basename>`
  reload failuje z `ImportError: parent not in sys.modules`. Zamiast tego
  każde wywołanie buduje świeży spec_from_file_location + module_from_spec
  + exec_module i podmienia wpis w sys.modules. Drugie wywołanie na tym
  samym pliku ładuje zmodyfikowaną zawartość.

Banner D-45: print `[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: <abspath>`
PRZED `exec_module`, na stdout — user widzi skąd kod nawet gdy import wybuchnie.

Wszystkie komunikaty błędów po polsku (PROJECT.md constraint).
Stdlib only: importlib.util + inspect + os + sys (D-46, D-47).
"""
import importlib.util
import inspect
import os
import sys


# Stałe modułu — SCREAMING_SNAKE_CASE per CONVENTIONS.md §Naming.
# 8 nazw parametrów sygnatury strategii (verbatim z PROMPT_DLA_AGENTA.txt i Phase 1 D-03).
EXPECTED_PARAMS = ('dev', 'l', 's', 'phi', 'kappa', 'rho', 'h', 'p')

# Wymagane klucze w STRATEGY_META (D-47 layer 4 + Phase 2 D-25 schema).
META_REQUIRED_KEYS = ('description', 'params', 'baseline_kpi')

# Prefiks namespace dla custom modułów (D-46 — sphsim.strategies.<X> zarezerwowane
# dla built-in, custom ładujemy do osobnego "syntetycznego" namespace'u).
CUSTOM_NAMESPACE_PREFIX = 'sphsim.custom'


class LoaderError(Exception):
    """Dowolny problem podczas ładowania custom strategii (D-48).

    Wywołujący (CLI main.py / REPL do_custom / do_run) wyciąga `e.args[0]`
    jako polski one-liner i drukuje do stderr (CLI) lub stdout (REPL).
    """
    pass


def _validate_meta(meta, abspath):
    """Walidacja STRATEGY_META (D-47 layer 4) — D-25 Phase 2 schema.

    Sprawdza w kolejności:
      1. Czy meta jest dict
      2. Czy zawiera wszystkie 3 wymagane klucze (description / params / baseline_kpi)
      3. Czy description jest str
      4. Czy params jest list
      5. Dla każdego tup w params: krotka 4-elementowa (name:str, type:callable, default, desc:str)
      6. Czy baseline_kpi jest dict albo None

    Każde naruszenie podnosi LoaderError z polskim komunikatem wskazującym konkret.
    """
    if not isinstance(meta, dict):
        type_name = type(meta).__name__
        raise LoaderError(
            f"STRATEGY_META w pliku {abspath} musi być dict, otrzymano {type_name}."
        )
    for required in META_REQUIRED_KEYS:
        if required not in meta:
            raise LoaderError(
                f"STRATEGY_META w pliku {abspath} brakuje klucza '{required}'."
            )
    if not isinstance(meta['description'], str):
        raise LoaderError(
            f"STRATEGY_META['description'] w pliku {abspath} musi być str, "
            f"otrzymano {type(meta['description']).__name__}."
        )
    if not isinstance(meta['params'], list):
        raise LoaderError(
            f"STRATEGY_META['params'] w pliku {abspath} musi być list, "
            f"otrzymano {type(meta['params']).__name__}."
        )
    for i, tup in enumerate(meta['params']):
        if not isinstance(tup, tuple) or len(tup) != 4:
            raise LoaderError(
                f"STRATEGY_META['params'][{i}] w {abspath} musi być krotką "
                f"4-elementową (name, type, default, description), otrzymano {tup!r}."
            )
        pname, ptype, _pdefault, pdesc = tup
        if not isinstance(pname, str):
            raise LoaderError(
                f"STRATEGY_META['params'][{i}][0] w {abspath} musi być str (nazwa), "
                f"otrzymano {type(pname).__name__}."
            )
        if not callable(ptype):
            raise LoaderError(
                f"STRATEGY_META['params'][{i}][1] w {abspath} musi być callable "
                f"(np. int, float, str), otrzymano {type(ptype).__name__}."
            )
        if not isinstance(pdesc, str):
            raise LoaderError(
                f"STRATEGY_META['params'][{i}][3] w {abspath} musi być str (opis), "
                f"otrzymano {type(pdesc).__name__}."
            )
    if meta['baseline_kpi'] is not None and not isinstance(meta['baseline_kpi'], dict):
        raise LoaderError(
            f"STRATEGY_META['baseline_kpi'] w pliku {abspath} musi być dict albo None, "
            f"otrzymano {type(meta['baseline_kpi']).__name__}."
        )


def load_custom(path):
    """Załaduj custom strategię z pliku .py i zwróć tuple `(basename, fn, meta)`.

    Loader jest **pure** (D-46) — NIE wstawia do `STRATEGIES`; rejestrację
    robi wywołujący (CLI main.py lub REPL do_custom). Walidacja 4-warstwowa
    (D-47) podnosi LoaderError z polskim komunikatem przy każdym z błędów —
    strategia NIE jest zwracana przy żadnym naruszeniu (fail-fast).

    Reload (D-38): drugie wywołanie na tym samym pliku ładuje świeżą zawartość
    przez nowy spec_from_file_location (NIE stdlib reload — RESEARCH Pitfall #1).
    """
    # ── 1. Path resolve + existence (D-36, RESEARCH Pitfall #4) ─────────────
    abspath = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(abspath):
        # Polski one-liner zamiast angielskiego FileNotFoundError z exec_module.
        raise LoaderError(f"Plik nie istnieje: {abspath}")

    # ── 2. Nazwa strategii (D-34) + collision check (D-49) ──────────────────
    basename = os.path.splitext(os.path.basename(abspath))[0]
    # Import w środku funkcji — unikamy circular import gdyby loader był
    # importowany podczas inicjalizacji pakietu sphsim.strategies.
    from sphsim.strategies import BUILTIN_STRATEGIES
    if basename in BUILTIN_STRATEGIES:
        raise LoaderError(
            f"Nazwa '{basename}' koliduje z wbudowaną strategią. Zmień nazwę pliku."
        )

    # ── 3. Banner pre-import (D-45) ─────────────────────────────────────────
    # Drukowany PRZED spec_from_file_location, na stdout — user widzi skąd kod
    # nawet gdy exec_module później wybuchnie.
    print(f"[OSTRZEŻENIE] Ładuję arbitralny kod Pythona z: {abspath}")

    # ── 4. Spec + exec (D-47 layer 1, RESEARCH Pitfall #2 / #3) ─────────────
    full_name = f'{CUSTOM_NAMESPACE_PREFIX}.{basename}'
    spec = importlib.util.spec_from_file_location(full_name, abspath)
    if spec is None or spec.loader is None:
        # Pitfall #3: pliki bez .py extension dają spec=None.
        raise LoaderError(
            f"Ścieżka {abspath} nie wygląda na plik Pythona (.py)."
        )
    mod = importlib.util.module_from_spec(spec)
    # Wpis w sys.modules MUSI być PRZED exec_module — jeśli moduł odwołuje się
    # sam do siebie podczas top-level (rzadkie, ale legit), exec nie wybuchnie.
    sys.modules[full_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        # Pitfall #2: cleanup zombie po failed exec — bez tego następne load_custom
        # na tym pliku dostałoby corrupted/partially-initialized module obj.
        sys.modules.pop(full_name, None)
        raise LoaderError(
            f"Błąd podczas importu pliku {abspath}: {type(e).__name__}: {e}"
        )

    # ── 5. Funkcja istnieje + callable (D-47 layer 2, Pitfall #5) ───────────
    # KRYTYCZNE: callable check MUSI być PRZED signature check.
    # `inspect.signature(NotCallable())` rzuca TypeError, nie LoaderError.
    fn_name = f'strategy_{basename}'
    fn = getattr(mod, fn_name, None)
    if not callable(fn):
        raise LoaderError(
            f"Brak funkcji '{fn_name}' w pliku {abspath}. Oczekiwana sygnatura: "
            f"{fn_name}({', '.join(EXPECTED_PARAMS)}) -> str."
        )

    # ── 6. Sygnatura: dokładnie 8 nazw lub *args escape (D-47 layer 3) ──────
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    has_var_pos = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
    if not has_var_pos:
        actual_names = tuple(p.name for p in params[:8])
        if actual_names != EXPECTED_PARAMS:
            raise LoaderError(
                f"Funkcja '{fn_name}' ma sygnaturę {sig}. "
                f"Oczekiwana: ({', '.join(EXPECTED_PARAMS)})."
            )

    # ── 7. STRATEGY_META validation (D-47 layer 4) ──────────────────────────
    meta = getattr(mod, 'STRATEGY_META', None)
    if meta is None:
        raise LoaderError(
            f"Plik {abspath} nie eksportuje STRATEGY_META (wymagane: dict z kluczami "
            f"description/params/baseline_kpi)."
        )
    _validate_meta(meta, abspath)

    # ── 8. Return tuple (D-46 — rejestrację robi wywołujący) ────────────────
    return basename, fn, meta


def parse_params_from_meta(tokens, meta, strategy_name):
    """Konwertuj tokeny `k=v` na dict z typami z STRATEGY_META['params'] (D-39/D-40/D-43).

    - Default values: z meta['params'] — populowane dla każdego parametru.
    - Token bez `=`: WARNING na stdout, kontynuacja (D-43 graceful — nie kill run'a).
    - Nieznany klucz: LoaderError z listą dostępnych (D-40).
    - Bad conversion: LoaderError z konkretną nazwą i typem.
    - Wartość z `=` w środku (np. `json_key=k=v`): split na PIERWSZY `=` (D-39).
    """
    # Mapa { nazwa: (typ_callable, default) }
    declared = {pname: (ptype, pdefault) for pname, ptype, pdefault, _ in meta['params']}
    # Populate defaults — będą nadpisane jeśli user poda k=v.
    out = {pname: pdefault for pname, (_ptype, pdefault) in declared.items()}

    warnings = []
    for tok in tokens:
        if '=' not in tok:
            # D-43 graceful: ostrzeżenie, ale loader kontynuuje (default zostaje).
            warnings.append(f"Pominięto token '{tok}' — oczekiwany format key=value.")
            continue
        # D-39: split na PIERWSZY `=` — wartość może zawierać `=`
        # (np. JSON-like strings przekazywane jako string param).
        key, raw_value = tok.split('=', 1)
        if key not in declared:
            available = ', '.join(declared.keys()) if declared else '(brak)'
            raise LoaderError(
                f"Nieznany parametr '{key}' dla strategii '{strategy_name}'. "
                f"Dostępne: {available}."
            )
        ptype, _default = declared[key]
        try:
            out[key] = ptype(raw_value)
        except (ValueError, TypeError):
            raise LoaderError(
                f"Nie można skonwertować '{raw_value}' na {ptype.__name__} "
                f"dla parametru '{key}'."
            )

    # Warnings drukujemy PO pełnym parsingu, żeby user dostał wszystkie naraz.
    for w in warnings:
        print(w)

    return out
