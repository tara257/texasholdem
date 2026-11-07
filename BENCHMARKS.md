# Validation and baseline results

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
