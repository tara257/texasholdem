# Version 3: final submission corrections

The final version keeps V2's betting strategy and makes two small fixes:

- A straight-draw bonus requires a hole-card rank that contributes beyond
  the board. Four connected board cards alone no longer provide that bonus.
- River bet sizing evaluates the chips an opponent can actually call when
  their remaining stack is below the minimum raise, then returns a legal
  raise total. A regression test covers a five-chip opponent and a legal
  twenty-chip raise; the uncalled excess is returned by the engine.

## Verification

- Full suite: **440 passed, 6 skipped**.
- Focused bot and model tests: **35 passed**.
- Submission checker: passed without source-review findings.
- Final paired regression: 200 deals per opponent, both seats, both
  versions, against all six baselines (**4,800 hands total**), seed 505.
  Every paired return matched V2 in this sample, and all faults were zero.

The regression run establishes no observed change on those sampled deals;
these specific corrections are demonstrated by the added regression tests.
This is not evidence of a broad increase in playing strength. Raw results
and source hashes are in `benchmark_v3.json`.

```sh
.venv/bin/python compare_bots.py --baseline /path/to/v2.pkl --deals 200 --seed 505
.venv/bin/python -m pytest tests test_bot.py -q
.venv/bin/python -m submit --team texasholdem
```

The final upload still consists of four files: `texasholdem.pkl`,
`model.py`, `poker_math.py`, and `river_policy.py`.

## Adaptation experiments

Broader decay and recent-activity variants were tested against V2 and
style-switching opponents. Fresh-deal gains were inconclusive, so those
strategy changes are not in the submitted bot. `stress_bots.py` retains
the two local test opponents for future evaluation; they alternate between
folding/shoving and calling/tight play every 40 hands. Test tooling is not
part of the submission.

---

# Version 2: measured improvements

Version 2 adds river bet sizing based on expected profit against likely
calling hands, separate preflop/river fold statistics, wider blind steals
against habitual folders, and larger value bets against habitual callers.
Opponent identity is not used to select a strategy; adjustments come from
observed actions.

## Direct matches against version 1

The original bot is commit `c73dbba`. Both versions played in isolated
workers with each deal replayed from both seats.

| Run | Seed | Hands | V2 profit vs V1 (bb/100, 95% interval) | Faults |
| --- | ---: | ---: | ---: | ---: |
| Initial screen | 101 | 1,000 | +43.4 ± 17.5 | 0 |
| Fresh-deal validation | 202 | 2,000 | +44.0 ± 13.4 | 0 |

The strategy was unchanged between these two runs.

## Paired comparisons against supplied opponents

Each version played 1,000 deals from both seats against each opponent:
2,000 hands per version per opponent, 24,000 hands total. Both versions
received identical decks and the opponent had the same random seed.
Changes and 95% intervals are computed from paired per-deal returns,
grouping both seat rotations before calculating uncertainty.

| Opponent | V1 bb/100 | V2 bb/100 | Paired change (95% interval) | Evidence |
| --- | ---: | ---: | ---: | --- |
| fold | +69.4 | +75.0 | +5.6 ± 1.2 | improved |
| call | +325.5 | +582.3 | +256.8 ± 37.8 | improved |
| random | +116.7 | +113.5 | -3.3 ± 36.9 | inconclusive |
| shove | +105.5 | +105.5 | +0.0 ± 0.0 | unchanged |
| tight | +48.9 | +71.8 | +22.9 ± 7.3 | improved |
| equity | +158.5 | +178.0 | +19.4 ± 19.1 | improved |

All compared bots recorded zero faults. The difference against `random`
is inconclusive, and the improvement against `equity` is marginal at this
sample size. The largest gain is against `call`. These tests support
retaining V2; they do not establish performance against unseen teams.

Raw scores, intervals, runtimes, configuration and SHA-256 hashes of the
tested candidate source are in `benchmark_v2.json`. To reproduce the
paired comparison, keep a version-1 pickle beside its original source
files, then run:

```sh
.venv/bin/python compare_bots.py --baseline /path/to/v1.pkl --deals 1000 --seed 202
```

## Version 2 correctness and submission

- Full suite: **436 passed, 6 skipped**.
- Focused model and bot regression tests: **31 passed**.
- Submission checker: passed, with no source-review findings.
- Upload all four files: `texasholdem.pkl`, `model.py`, `poker_math.py`,
  and **`river_policy.py`**. Regenerate the pickle after changing code.

The river response model is approximate: it does not solve opponent
reraising or model future decisions. Runtime and results will vary on the
organiser's machine.

---

# Version 1: original validation and baseline results

Measured on 7 November 2026 with Python 3.14.5 and Pydantic 2.14.3.

## Independent-deal benchmark

```sh
.venv/bin/python -m evals --deals 1000 --seed 37
```

Each of the 1,000 deals is replayed with seats swapped: 2,000 hands per
opponent and 12,000 hands in total. The intervals below are the evaluation
harness's reported 95% confidence intervals, shown as estimate ± half-width.

| Opponent | Profit (bb/100) | Verdict | Hands | Faults | Slowest move |
| --- | ---: | --- | ---: | ---: | ---: |
| fold | +67.6 ± 1.4 | ahead | 2,000 | 0 | 0.02 s |
| call | +334.0 ± 30.4 | ahead | 2,000 | 0 | 0.12 s |
| random | +89.5 ± 32.4 | ahead | 2,000 | 0 | 0.08 s |
| shove | +190.4 ± 52.1 | ahead | 2,000 | 0 | 0.02 s |
| tight | +49.7 ± 8.8 | ahead | 2,000 | 0 | 0.06 s |
| equity | +186.9 ± 26.8 | ahead | 2,000 | 0 | 0.05 s |

These are results against the supplied baseline bots, not predictions of
results against other teams. Runtime depends on the organiser's machine.
No strategy changes were made between the initial seed-0 smoke benchmark
(200 deals per opponent) and this larger seed-37 run.

## Correctness and submission checks

```sh
.venv/bin/python -m pytest tests test_bot.py -q
# 431 passed, 6 skipped

.venv/bin/python -m submit --team texasholdem
# Played legally; no source-review findings or pickle violations.
```

The bot-specific and official model tests account for 26 passing tests.
The custom evaluator was checked against the official evaluator on 4,500
random hands, plus explicit edge cases. The full suite includes upstream
engine, worker and event-tool tests as well as our bot checks.

The validated submission consists of `texasholdem.pkl`, `model.py`, and
`poker_math.py`. The generated pickle stays local; regenerate it with the
command above when cloning this repository.
