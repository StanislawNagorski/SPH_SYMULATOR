"""Phase 6: Generowanie wykresów PNG (PLOT-01, PLOT-02). Backend='Agg' — headless safe.

Dwie publiczne funkcje:
  - plot_decision_distribution(ic_per_phase, veto_per_phase, abstain_per_phase, path)
    Słupkowy COMMIT/ABSTAIN/VETO per faza (PLOT-01).
  - plot_kpi_timeseries(history, T, path)
    Linowy avg_val + avg_providers per cykl z zaznaczonym oknem ostatnich 100
    cykli (PLOT-02).

Każda funkcja używa Agg backendu, zamyka figurę w finally (Pitfall 5
matplotlib memory leak), i pisze PNG przez fig.savefig(path).
"""
import matplotlib
matplotlib.use('Agg')          # MUST be before pyplot import — Pitfall 1
import matplotlib.pyplot as plt
import numpy as np

# Pitfall 7 — defensive font fallback (DejaVu Sans wspiera ą ę ł ń ó ś ź ż).
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'sans-serif']


def plot_decision_distribution(ic_per_phase, veto_per_phase, abstain_per_phase, path):
    """PLOT-01: grouped bar chart COMMIT/ABSTAIN/VETO per faza.

    Args:
        ic_per_phase: dict[int, dict] — z sim.run()['ic_per_phase']; klucz 'commits'.
        veto_per_phase: dict[int, int] — z sim.run()['veto_per_phase'].
        abstain_per_phase: dict[int, int] — z sim.run()['abstain_per_phase']
                           (Phase 6 PLOT-01, Plan 01 data gap fix).
        path: pathlib.Path | str — gdzie zapisać PNG.

    Side effects:
        Zapisuje PNG pod `path` (matplotlib `Agg` backend). Zamyka figurę w finally.
    """
    ic_per_phase = ic_per_phase or {}
    veto_per_phase = veto_per_phase or {}
    abstain_per_phase = abstain_per_phase or {}

    phases = sorted(
        set(ic_per_phase.keys())
        | set(veto_per_phase.keys())
        | set(abstain_per_phase.keys())
    )
    if not phases:
        phases = [1, 2, 3, 4]  # safety dla pustych runs — wciąż chcemy PNG (nie crash)

    commits = [
        ic_per_phase.get(p, {}).get('commits', 0) if isinstance(ic_per_phase.get(p), dict) else 0
        for p in phases
    ]
    abstains = [abstain_per_phase.get(p, 0) for p in phases]
    vetos    = [veto_per_phase.get(p, 0)    for p in phases]

    x = np.arange(len(phases))
    w = 0.27

    fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
    try:
        ax.bar(x - w, commits,  w, label='COMMIT',  color='#2E7D32')
        ax.bar(x,     abstains, w, label='ABSTAIN', color='#757575')
        ax.bar(x + w, vetos,    w, label='VETO',    color='#C62828')
        ax.set_xlabel('Faza urządzenia')
        ax.set_ylabel('Liczba decyzji')
        ax.set_title('Rozkład decyzji per faza')
        ax.set_xticks(x)
        ax.set_xticklabels([f'Faza {p}' for p in phases])
        ax.legend(loc='upper right')
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        fig.tight_layout()
        fig.savefig(path)
    finally:
        plt.close(fig)


def plot_kpi_timeseries(history, T, path):
    """PLOT-02: twin-axis line chart avg_val + avg_providers w funkcji cyklu.

    Args:
        history: dict — wymaga kluczy 'val' (list[float] len=T) i
                 'providers' (list[int] len=T). Z sim.run()['history'].
        T: int — liczba cykli (z args.T) — używana do okna last-100 (T-99..T).
        path: pathlib.Path | str — gdzie zapisać PNG.

    Side effects:
        Zapisuje PNG pod `path`. Zamyka figurę w finally. Jeśli history jest
        puste lub brakuje kluczy, funkcja zwraca cicho bez zapisu (defensive —
        write_report może wtedy zalogować disclaimer na stderr).
    """
    if not history or 'val' not in history or 'providers' not in history:
        return
    val = history['val']
    providers = history['providers']
    if not val or not providers:
        return

    cycles = list(range(1, len(val) + 1))
    fig, ax1 = plt.subplots(figsize=(10, 5), dpi=120)
    try:
        color_val = '#1565C0'
        ax1.set_xlabel('Cykl symulacji')
        ax1.set_ylabel('avg_val (waluacja Konsumentów)', color=color_val)
        ax1.plot(cycles, val, color=color_val, linewidth=0.8, alpha=0.85, label='avg_val')
        ax1.tick_params(axis='y', labelcolor=color_val)

        ax2 = ax1.twinx()
        color_prov = '#EF6C00'
        ax2.set_ylabel('avg_providers (liczba dostawców)', color=color_prov)
        ax2.plot(cycles, providers, color=color_prov, linewidth=0.8, alpha=0.85, label='avg_providers')
        ax2.tick_params(axis='y', labelcolor=color_prov)

        # Last-100 window — shaded grey (PLOT-02 SC requirement).
        last100_start = max(1, T - 99)
        ax1.axvspan(last100_start, T, alpha=0.15, color='grey')

        fig.suptitle('Przebieg KPI w czasie symulacji (zaznaczone ostatnie 100 cykli)')
        fig.tight_layout()
        fig.savefig(path)
    finally:
        plt.close(fig)
