# Our Texas Hold'em bot

Public fork: https://github.com/tara257/texasholdem

`model.py` contains our strategy. `poker_math.py` contains the fast hand
ranking, range features and equity calculation. `river_policy.py` chooses
river bet sizes using an approximate opponent-response model. The organiser's engine and
public API files are unchanged.

## Get started

Use Python 3.10 or newer and run commands from this repository's root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/test_model.py test_bot.py -q
.venv/bin/python -m evals --deals 1000 --seed 37
```

The pinned dependencies are the competition's own. The bot needs no extra
packages, network requests, API keys, model downloads or runtime files.

## Strategy

- **Preflop:** open wider on the button, isolate limps with stronger hands,
  and choose calls and reraises using equity and effective pot odds.
- **Opponent ranges:** maintain weights over possible hole-card pairs.
  Calls and raises update those weights using hand-strength features and
  observed aggression. Known cards are removed before equity calculation.
- **Postflop:** simulate remaining cards against those weighted ranges;
  heads-up river equity enumerates all possible opponent hands exactly
  for the inferred range. Bet strong holdings and occasionally semi-bluff
  draws or bluff opponents who fold frequently. On the river, compare
  checking with several bet sizes using fold probability and equity
  specifically against hands likely to call.
- **Adaptation:** keep smoothed aggression, calling and folding statistics
  by team name across hands. `seed()` resets only hand-specific data.
- **Exploitation:** use preflop fold statistics to steal more blinds from
  habitual folders; value-shove suitable hands against opponents with
  enough observed calls and almost no folds or raises.
- **Reliability:** respect the supplied raise range, return integer street
  totals, check when raising is unavailable, and correct heads-up pot odds
  for an overbet we cannot fully call. Sampling loops are bounded.

This is a heuristic poker bot, not a game-theoretic solver or a trained
neural network. Its inferred ranges can be wrong. Multiway range sampling
is approximate; the strategy is primarily designed for heads-up play.
Baseline results do not establish an edge against other teams.

## Tests

```sh
# Bot validity, evaluator correctness and regression checks
.venv/bin/python -m pytest tests/test_model.py test_bot.py -q

# All upstream tests plus our tests
.venv/bin/python -m pytest tests test_bot.py -q

# Larger benchmark on different deals (seats are swapped)
.venv/bin/python -m evals --deals 1000 --seed 37
```

Our tests compare 4,500 random 5-, 6- and 7-card hands against the official
evaluator, cover ranking edge cases, weighted river equity, blockers,
split pots, short all-in calls, legal raises, pickle round trips and
opponent memory. The organiser's model tests also exercise multiway and
short-stack games inside isolated worker processes.

## Prepare the submission

```sh
.venv/bin/python -m submit --team texasholdem
```

`texasholdem` is the current package name. Replace it with your actual team
name if different (lowercase letters, digits, hyphens and underscores).
The command creates the pickle, checks the source, and verifies it from a
clean staging directory. It does **not** upload anything.

The live Google Form asks for the public GitHub repository URL. All four
files listed by the command are committed at the root of this repository:

- `texasholdem.pkl` (or your chosen team's `.pkl`)
- `model.py`
- `poker_math.py`
- `river_policy.py`

Use the submission form linked from https://poker-arena-site.vercel.app/#/submit.
The published event schedule lists submissions from 16:00 to 18:00.
Regenerate the pickle and rerun validation after any strategy changes.
The validated `texasholdem.pkl` is committed alongside its Python source.
After changes, regenerate it, validate it, and commit/push the full bundle
before submitting the repository link. See `SUBMISSION.md` for the entry point.

## Current validation

The final refinement passed **440 tests, with 6 skipped**, including 35
focused bot tests. Its four-file submission passed validation without source-review
findings. The submitted strategy is version 2 with two small corrections:
straight-draw bonuses require a private card contribution, and river value
bets handle opponents whose remaining stack is below the minimum raise. `BENCHMARKS.md` records fresh-deal matches against version 1 and
paired comparisons against all six supplied baselines.

To compare against a frozen older submission stored with its original
source files:

```sh
.venv/bin/python compare_bots.py --baseline /path/to/v1.pkl --deals 1000 --seed 202
```

The comparison uses the same deals and opponent random seeds for both
versions, groups both seat rotations per deal, and reports confidence
intervals on the paired improvement. `compare_bots.py` is local test
tooling and is not submitted. `stress_bots.py` provides two additional
local opponents that alternate playing styles every 40 hands. The broader
adaptation experiments were not retained because fresh-deal improvements
were inconclusive.

## Original build (version 1)

On 7 November 2026, using Python 3.14.5 and the competition's pinned
Pydantic version, the full test run completed with **431 passed and 6
skipped**. The submission checker accepted the three-file package without
source-review findings. The initial benchmark (seed 0, 200 deals replayed
from both seats) finished ahead of all six supplied opponents with zero
faults. See `BENCHMARKS.md` for version 1 results and the subsequent version 2
comparison on fresh deals, followed by the final correction checks.
