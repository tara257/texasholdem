# Competition submission

Repository: https://github.com/tara257/texasholdem

The validated submission is committed at the repository root:

| File | Purpose |
| --- | --- |
| [texasholdem.pkl](texasholdem.pkl) | Initial `model.Model` object, pickled with protocol 4 |
| [model.py](model.py) | Bot callbacks and strategy |
| [poker_math.py](poker_math.py) | Hand ranking and equity calculations |
| [river_policy.py](river_policy.py) | River bet sizing |

The engine calls `seed(hand, player_id)` before a hand and
`run(actions, game_state)` for each decision. The latter returns a
`PlayerAction`. `end_game(actions, game_state)` records opponent statistics.

The bot uses the supplied public API and standard library. The organiser's
engine and API files are unchanged. No external weights or runtime data
files are needed.

Rebuild and validate from the repository root:

```sh
.venv/bin/python -m submit --team texasholdem
```

The submission checker passes without source-review findings. Full test
results: **440 passed, 6 skipped**. Details are in [BENCHMARKS.md](BENCHMARKS.md).

The live submission form requests a repository link. Enter the repository
URL above and the team's details in the form linked from the
[competition submission page](https://poker-arena-site.vercel.app/#/submit).
