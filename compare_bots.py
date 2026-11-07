"""Compare the current bot with a frozen pickle on identical duplicate deals.

Local evaluation tooling only; this file is not part of the submission.
Example: python compare_bots.py --baseline /path/to/v1.pkl --deals 1000
"""
import argparse
import json
import pickle
import shutil
import tempfile
from pathlib import Path

from arena.match import MatchConfig, play_match
from arena.players import Player, player
from evals.score import score
from evals.stats import ci95, mean_and_se
from model import Model
from submit import local_modules


def deck_returns(log):
    totals = [0.0] * log.config.deals
    for hand in log.hands:
        seat = hand.seats.index('candidate')
        totals[hand.deal] += hand.net[seat] / (len(log.names) * log.config.big_blind)
    return totals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--deals', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=202)
    parser.add_argument('--opponents', nargs='+', default=['fold', 'call', 'random', 'shove', 'tight', 'equity'])
    parser.add_argument('--out', default=str(Path(tempfile.gettempdir()) / 'texasholdem-comparison.json'))
    args = parser.parse_args()
    config = MatchConfig(deals=args.deals, seed=args.seed)
    rows = []
    with tempfile.TemporaryDirectory(prefix='poker-compare-') as folder:
        # Freeze the candidate source alongside its pickle, so later edits
        # cannot change the policy midway through a long comparison.
        root = str(Path(__file__).resolve().parent)
        for source in local_modules({'model'}, root):
            shutil.copy2(source, Path(folder) / Path(source).name)
        pkl = Path(folder) / 'candidate.pkl'
        pkl.write_bytes(pickle.dumps(Model(), protocol=4))
        print('opponent       old bb/100   new bb/100       paired change (95% CI)   faults', flush=True)
        for opponent in args.opponents:
            logs = [play_match([Player('candidate', path), player(opponent)], config)
                    for path in (args.baseline, str(pkl))]
            results = [score([log]) for log in logs]
            old, new = map(deck_returns, logs)
            mean, se = mean_and_se([b - a for a, b in zip(old, new)])
            row = dict(opponent=player(opponent).name, baseline=results[0].bb_per_100[0],
                       candidate=results[1].bb_per_100[0], delta=100 * mean,
                       delta_ci95=100 * ci95(se, len(old)),
                       baseline_ci95=results[0].ci95[0], candidate_ci95=results[1].ci95[0],
                       baseline_faults=results[0].faults[0], candidate_faults=results[1].faults[0],
                       hands_per_version=results[0].hands,
                       max_seconds=results[1].max_move_seconds[0])
            rows.append(row)
            print(f"{row['opponent']:<12} {row['baseline']:>+10.1f} {row['candidate']:>+12.1f} "
                  f"{row['delta']:>+12.1f} ± {row['delta_ci95']:<8.1f} "
                  f"{row['baseline_faults']}/{row['candidate_faults']}", flush=True)
            Path(args.out).write_text(json.dumps(dict(seed=args.seed, deals=args.deals, rows=rows), indent=2) + '\n')
            if any(result.faults[0] for result in results):
                raise RuntimeError('A compared bot faulted; see the match results before continuing.')


if __name__ == '__main__':
    main()
