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


def plot_batch_aggregate(per_seed_kpis, path):
    """PLOT-04: 5 subplotów (1×5 grid) z box-plotami dla każdego z 5 KPI.

    Args:
        per_seed_kpis: list[dict[str, float]] — N dictów z 5 kluczami z KPIS
                       (canonical order: avg_val_last100, cum_val_total,
                        avg_net_profit, delivery_ratio, avg_providers_l100).
        path: pathlib.Path | str — gdzie zapisać PNG.

    Side effects:
        Zapisuje PNG pod `path`. Zamyka figurę w finally (Pitfall 1 — matplotlib FD leak).
        Defensive: gdy per_seed_kpis pusta, funkcja zwraca cicho bez zapisu.

    Notes:
        5 subplotów (NIE jeden grouped boxplot) bo 5 KPI mają drastycznie różne skale
        (avg_val_last100≈92, cum_val_total≈92000, delivery_ratio≈0.79). Jedna Y-oś
        kompresowałaby delivery_ratio do niewidocznej linii. RESEARCH §F.13 — verified.

        Wywołanie `plt.subplots(1, 5, figsize=(15, 4), dpi=120)` jest load-bearing
        (Warning #6 contract): TestBatchPlots.test_5_panels mockuje plt.subplots
        i assertuje (nrows, ncols) == (1, 5).
    """
    if not per_seed_kpis:
        return

    KPI_LABELS = [
        ('avg_val_last100',     'avg_val_last100\n(waluacja, last 100)'),
        ('cum_val_total',       'cum_val_total\n(suma waluacji)'),
        ('avg_net_profit',      'avg_net_profit\n(zysk netto / urządzenie)'),
        ('delivery_ratio',      'delivery_ratio\n(% udanych)'),
        ('avg_providers_l100',  'avg_providers_l100\n(śr. dostawcy, last 100)'),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(15, 4), dpi=120)
    try:
        for ax, (kpi_key, label) in zip(axes, KPI_LABELS):
            values = [d[kpi_key] for d in per_seed_kpis]
            ax.boxplot(values, vert=True, patch_artist=True,
                       boxprops=dict(facecolor='#90CAF9'),
                       medianprops=dict(color='#0D47A1', linewidth=2))
            ax.set_title(label, fontsize=10)
            ax.set_xticks([])
            ax.grid(axis='y', linestyle='--', alpha=0.4)
            # Y-axis percent formatter dla delivery_ratio (matplotlib FuncFormatter
            # wymaga 2-arg lambda: (value, pos)).
            if kpi_key == 'delivery_ratio':
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
        fig.suptitle(f'Box-ploty 5 KPI (N={len(per_seed_kpis)} seedów)', fontsize=12)
        fig.tight_layout()
        fig.savefig(path)
    finally:
        plt.close(fig)
