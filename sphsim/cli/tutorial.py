"""Phase 8 tutorial state machine — TutorialFlow + STEP_TOPICS + STEP_TASKS + check_step.

NO I/O, NO sphsim.* imports — pure state machine + pure dispatch table.

Module ownership (Plan 08-03 contract):
  * TutorialStep   — dataclass, static description for one tutorial step (1..8).
  * TutorialFlow   — dataclass, mutable per-session state owned by SPHShell.
  * STEP_TOPICS    — dict[int, str], step number → directory slug.
  * STEP_TASKS     — dict[int, TutorialStep], step number → static content.
  * check_step()   — pure function, verifies whether the user's command satisfies
                     the current step per RESEARCH §Step Verification Map.

Consumed by Plan 08-04 (`repl.py`): `do_tutorial` instantiates `TutorialFlow()`,
`postcmd` dispatches to `check_step(...)`, and `do_run/do_compare/do_batch`
use `self._tutorial_state.step_report_dir(topic)` as `report_dir_override`.

`strategies_keys` and `builtin_strategies` are passed AS ARGUMENTS to check_step
(not imported here) — this keeps tutorial.py decoupled from the strategies
registry and avoids the circular import that would arise if tutorial.py and
repl.py both imported the strategies registry while tutorial.py was also being
imported by repl.py.

All Polish copy strings are verbatim per RESEARCH §Polish Tone Calibration
(lines 481-512) with Open Question #2 (step 6) and #3 (step 7) resolutions
embedded.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Set


# STEP_TOPICS — int step number → directory slug used by step_report_dir.
# Order MUST match RESEARCH §Step Verification Map (lines 439-452).
STEP_TOPICS = {
    1: 'baseline',
    2: 'strategies',
    3: 'run-strategy',
    4: 'custom',
    5: 'compare',
    6: 'env',
    7: 'report',
    8: 'batch',
}


@dataclass
class TutorialStep:
    """Static content for one tutorial step.

    Fields are pure data — no methods, no mutation. Instances live as values
    in the module-level `STEP_TASKS` dict and are read-only at runtime.
    """
    step_num: int
    topic: str
    title: str
    description: str
    expected_command_hint: str


# STEP_TASKS — int step → TutorialStep with verbatim Polish copy.
# Source: RESEARCH §Polish Tone Calibration sample lines 484-512.
# Tone: informal-respectful ("ty" implicit), short sentences, direct verbs.
STEP_TASKS = {
    1: TutorialStep(
        step_num=1,
        topic='baseline',
        title='Baseline',
        description=(
            "Uruchom symulację baseline dla strategii naive:\n"
            "\n"
            "  run naive zeta=0.75\n"
            "\n"
            "To podstawowy punkt odniesienia (KPI = 92) — wszystkie\n"
            "późniejsze strategie porównujemy do tego wyniku."
        ),
        expected_command_hint='run naive zeta=0.75',
    ),
    2: TutorialStep(
        step_num=2,
        topic='strategies',
        title='Lista strategii',
        description=(
            "Wyświetl listę strategii i szczegóły jednej z nich:\n"
            "\n"
            "  strategies\n"
            "  strategy incentive\n"
            "\n"
            "W odpowiedzi zobaczysz opis, parametry i baseline KPI."
        ),
        expected_command_hint='strategies',
    ),
    3: TutorialStep(
        step_num=3,
        topic='run-strategy',
        title='Inna strategia',
        description=(
            "Uruchom inną wbudowaną strategię, np.:\n"
            "\n"
            "  run incentive expected_P=30\n"
            "  run adaptive s_target=15\n"
            "\n"
            "Sprawdź czy avg_val_last100 różni się od baseline (92)."
        ),
        expected_command_hint='run incentive expected_P=30',
    ),
    4: TutorialStep(
        step_num=4,
        topic='custom',
        title='Custom strategia',
        description=(
            "Załaduj przykładowy szablon custom strategii:\n"
            "\n"
            "  custom examples/custom_strategy_template.py\n"
            "\n"
            "Strategia zostanie dodana do listy (zobaczysz ją w `strategies`).\n"
            "Loader wykonuje arbitralny Python z pliku — to twoja strategia,\n"
            "twoja odpowiedzialność."
        ),
        expected_command_hint='custom examples/custom_strategy_template.py',
    ),
    5: TutorialStep(
        step_num=5,
        topic='compare',
        title='Porównanie z agentem',
        description=(
            "Porównaj strategię z agentem racjonalnym i bez niego:\n"
            "\n"
            "  compare incentive expected_P=30\n"
            "\n"
            "Zobaczysz tabelę delta KPI: z agentem (default) vs bez (--no-agent).\n"
            "Dla incentive expected_P=30 agent powinien chronić zysk\n"
            "(empiryczny dowód incentive compatibility)."
        ),
        expected_command_hint='compare incentive expected_P=30',
    ),
    6: TutorialStep(
        step_num=6,
        topic='env',
        title='Override środowiska (informacyjny)',
        description=(
            "REPL nie pozwala override'ować środowiska — to robi CLI.\n"
            "Możesz spróbować później w dowolnym shellu:\n"
            "\n"
            "  python sph_sim.py --strategy incentive --phi 0.5 --rho 0.3 \\\n"
            "                    --valuation step --seed 42 --no-agent\n"
            "\n"
            "Wynik będzie się różnił od baseline (krok 1) — to dowód że\n"
            "środowisko ma wpływ. To krok informacyjny — wpisz cokolwiek\n"
            "(np. `skip` lub `repeat`) żeby ruszyć dalej."
        ),
        expected_command_hint=(
            'python sph_sim.py --strategy incentive --phi 0.5 --rho 0.3 '
            '--valuation step --seed 42 --no-agent'
        ),
    ),
    7: TutorialStep(
        step_num=7,
        topic='report',
        title='Inspekcja raportu',
        description=(
            "Otwórz raport z poprzedniego kroku (krok 5 lub 6). Polecane:\n"
            "\n"
            "  cat reports/<najnowszy>/report.md | head -40\n"
            "\n"
            "(w drugim terminalu, ten REPL zostawia stan jak jest).\n"
            "Zobaczysz: konfigurację, parametry, tabelę KPI, rozkład decyzji,\n"
            "porównanie z baseline. Wpisz `skip` żeby ruszyć dalej."
        ),
        expected_command_hint='skip',
    ),
    8: TutorialStep(
        step_num=8,
        topic='batch',
        title='Batch + agregat',
        description=(
            "Uruchom strategię na wielu seedach i zobacz agregat statystyczny:\n"
            "\n"
            "  batch naive --seeds 5 zeta=0.75\n"
            "\n"
            "Otrzymasz mean/std/min/max/95% CI dla 5 KPI + wykres box-plot\n"
            "(batch_aggregate.png). Strategia bije baseline jeśli 95% CI dla\n"
            "avg_val_last100 leży powyżej 92."
        ),
        expected_command_hint='batch naive --seeds 5 zeta=0.75',
    ),
}


@dataclass
class TutorialFlow:
    """Mutable per-session tutorial state. Owned by SPHShell (one instance per
    `do_tutorial` invocation). Persisted only in process memory — no
    serialization, no filesystem state.

    Fields per RESEARCH §Pattern 1 (lines 178-193):
      * step          — current step number (1..8), advances via postcmd / skip.
      * total         — total step count (constant = 8 for Phase 8).
      * session_ts    — UTC-naive timestamp used in tutorial report dir name;
                        format `YYYYMMDD-HHMMSS` matches existing report dir
                        convention in sphsim.report.
      * hint_count    — count of hints emitted for the current step; reset to 0
                        on step transition. Used by repl.py `_show_step_hint`.
      * MAX_HINTS     — cap on hints per step before postcmd auto-advances.
    """
    step: int = 1
    total: int = 8
    session_ts: str = field(default_factory=lambda: datetime.now().strftime('%Y%m%d-%H%M%S'))
    hint_count: int = 0
    MAX_HINTS: int = 3

    @property
    def base_report_dir(self) -> Path:
        """Root directory for this tutorial session's reports: `reports/tutorial-<ts>/`."""
        return Path('reports') / f'tutorial-{self.session_ts}'

    def step_report_dir(self, topic: str) -> Path:
        """Per-step report directory: `<base>/step-<n>-<topic>/`.

        Used by repl.py `do_run/do_compare/do_batch` as `report_dir_override`
        when `self._tutorial_state is not None`.
        """
        return self.base_report_dir / f'step-{self.step}-{topic}'


def check_step(
    step_n: int,
    line: str,
    last_sim_result: Optional[dict],
    strategies_keys: Set[str],
    builtin_strategies: frozenset,
    tutorial_flow: Optional['TutorialFlow'] = None,
) -> bool:
    """Verify the user's last REPL line satisfied step `step_n`.

    Pure function — no I/O, no print, no exceptions. Returns True if the user
    accomplished the step, False otherwise. Maps RESEARCH §Step Verification
    Map (lines 439-452) row-by-row.

    Args:
        step_n: tutorial step number (1..8).
        line: raw text the user typed in the REPL (whitespace-stripped here).
        last_sim_result: dict result of the last simulation
            (do_run → sim res dict; do_compare → res_combined; do_batch →
            aggregate + per_seed; None for steps that don't run a simulator).
        strategies_keys: live keys of `sphsim.strategies.STRATEGIES` AT CALL
            TIME, snapshotted by repl.py postcmd. Used only by step 4 to
            detect custom-strategy registration.
        builtin_strategies: `sphsim.strategies.BUILTIN_STRATEGIES` frozenset.
        tutorial_flow: TutorialFlow instance (unused in this implementation;
            kept in signature for forward-compat with future steps that may
            inspect mutable state, e.g. hint_count gates).

    Returns:
        True iff the step's verification criteria are satisfied.
    """
    line = (line or '').strip()
    tokens = line.split()

    # Step 1 (baseline) — `run naive ...` AND avg_val_last100 >= 80.0.
    if step_n == 1:
        return (
            len(tokens) >= 2 and tokens[0] == 'run' and 'naive' in tokens
            and last_sim_result is not None
            and last_sim_result.get('avg_val_last100', 0) >= 80.0
        )

    # Step 2 (strategies) — display-only; pass when the user types the listing
    # command or asks for a single strategy. No simulator dependency.
    if step_n == 2:
        return line == 'strategies' or line.startswith('strategy ')

    # Step 3 (run-strategy) — run + builtin name + simulator produced a result.
    if step_n == 3:
        return (
            len(tokens) >= 2 and tokens[0] == 'run'
            and tokens[1] in builtin_strategies
            and last_sim_result is not None
            and last_sim_result.get('avg_val_last100', None) is not None
        )

    # Step 4 (custom) — pass iff STRATEGIES now contains a non-builtin key.
    # Shape check on `line` is intentionally skipped: postcmd has already
    # mutated STRATEGIES via do_custom; checking the diff is more reliable
    # than parsing the command line (the user may have reload-loaded an
    # existing custom under a different alias).
    if step_n == 4:
        return bool(set(strategies_keys) - set(builtin_strategies))

    # Step 5 (compare) — `compare ...` AND comparison.delta is truthy.
    # Empty delta dict ({}) is intentionally False: it means do_compare ran
    # but produced no real KPI diff (e.g. agent-only side errored).
    if step_n == 5:
        return bool(
            tokens and tokens[0] == 'compare'
            and last_sim_result is not None
            and 'comparison' in last_sim_result
            and last_sim_result['comparison'].get('delta')
        )

    # Step 6 (env) — Open Question #2 resolution: soft-pass informational step.
    # The displayed command is for the user to try LATER in a separate shell;
    # the REPL doesn't run it. Any non-empty line advances the tutorial.
    if step_n == 6:
        return bool(line)

    # Step 7 (report) — Open Question #3 resolution: soft-pass display step.
    # User is encouraged to `cat` the report in a second terminal; any input
    # advances. Same shape as step 6.
    if step_n == 7:
        return bool(line)

    # Step 8 (batch) — `batch ... --seeds ...` AND aggregate dict in result.
    if step_n == 8:
        return bool(
            tokens and tokens[0] == 'batch' and '--seeds' in line
            and last_sim_result is not None
            and 'aggregate' in last_sim_result
        )

    # Unknown step number — defensive False (postcmd should never reach here
    # because step is clamped to 1..total in repl.py, but explicit > implicit).
    return False
