"""Bot-specific checks; run alongside the organiser's tests/test_model.py."""
import pickle
import random

import pytest

from card_utils import Card, evaluate, full_deck
from game_state import GameState, GameStateView
from model import Model
from player_action import PlayerAction
from poker_math import encode, rank_hand, sample_equity


def cards(text):
    return [Card.parse(c) for c in text.split()]


def encoded(text):
    return [encode(c) for c in cards(text)]


@pytest.mark.parametrize('size', [5, 6, 7])
def test_fast_evaluator_matches_organiser(size):
    rng = random.Random(930 + size)
    deck = full_deck()
    for _ in range(1500):
        hand = rng.sample(deck, size)
        assert rank_hand([encode(c) for c in hand]) == evaluate(hand)


@pytest.mark.parametrize('text', [
    'AS 2S 3S 4S 5S KD QD',  # wheel straight flush
    'AS AH AD KS KH KD 2C',  # two trips: best full house
    '2C 2D 2H 2S AC KH QD',  # quad kickers
    'AC AD KC KD QC QD 2S',  # three pairs: third pair can supply kicker
    'AS QS 9S 7S 5S 3S 2S',  # seven-card flush
    'AS 2D 3H 4C 5S 6D 7H',  # seven-high beats wheel
    'AS AH AD 2C 3D 4H 5C',  # straight beats trips
])
def test_evaluator_edge_cases(text):
    hand = cards(text)
    assert rank_hand([encode(c) for c in hand]) == evaluate(hand)


def test_river_board_tie_splits_pot():
    board, hand = encoded('AS KS QS JS TS'), encoded('2C 3D')
    pair = tuple(encoded('4H 5H'))
    ranges = [([pair], [1.0])]
    assert sample_equity(hand, board, ranges, random.Random(1)) == 0.5
    ranges.append(([tuple(encoded('6D 7D'))], [1.0]))
    assert sample_equity(hand, board, ranges, random.Random(1), 30) == pytest.approx(1 / 3)


def test_exact_river_equity_respects_weights_and_blockers():
    hand, board = encoded('AS AH'), encoded('2C 3D 7H 9S KC')
    # AA beats QQ, loses to KK; the third combination is impossible.
    hands = [tuple(encoded(t)) for t in ('QC QD', 'KH KD', 'AS AD')]
    result = sample_equity(hand, board, [(hands, [3.0, 1.0, 1000.0])], random.Random(1))
    assert result == pytest.approx(0.75)


def test_preflop_sampling_sanity():
    result = sample_equity(encoded('AS AH'), [],
                           [([tuple(encoded('KC KD'))], [1.0])],
                           random.Random(123), 2000)
    assert 0.77 < result < 0.87


def test_short_call_excludes_uncallable_overbet():
    state = GameState([500, 100])
    state.process_action(PlayerAction.raise_to(0, 500))
    bot = Model()
    bot.seed(cards('AS KD'), 1)
    bot._observe([PlayerAction.raise_to(0, 500)], GameStateView(state))
    # We pay 80 to contest a final 200, not the uncallable 600.
    action = bot._decide(GameStateView(state), [0], [], 0.39, random.Random(1))
    assert action.kind == 'fold'
    action = bot._decide(GameStateView(state), [0], [], 0.43, random.Random(1))
    assert action.kind == 'call'


def test_raise_is_clamped_and_uses_integer_street_total():
    state = GameState([500, 500])
    view = GameStateView(state)
    bot = Model()
    bot.seed(cards('AS AH'), 0)
    for requested in (-5, 42.5, 99999):
        action = bot._raise(view, requested)
        state.validate_action(action)
        assert type(action.amount) is int
    state.process_action(PlayerAction.raise_to(0, 500))
    bot.player_id = 1
    assert bot._raise(view, 99999).kind == 'call'


def test_history_counted_once_and_learning_survives_seed():
    state = GameState([500, 500], teams=['us', 'villain'])
    view = GameStateView(state)
    bot = Model()
    bot.seed(cards('AS AH'), 0)
    bot._observe([], view)
    action = PlayerAction.raise_to(0, 50)
    reply = PlayerAction.fold(1)
    state.process_action(action)
    state.process_action(reply)
    bot.end_game([action, reply], view)
    stats = dict(bot.opponents['villain'])
    assert stats['hands'] == stats['folds'] == stats['faced'] == stats['decisions'] == 1
    bot.seed(cards('KC QD'), 1)
    assert bot.opponents['villain'] == stats
    assert bot.seen_board == [] and bot.preflop_raises == 0


def test_pickle_replays_same_decision():
    bot = Model()
    clone = pickle.loads(pickle.dumps(bot, protocol=4))
    state = GameStateView(GameState([500, 500]))
    hand = cards('JC TD')
    bot.seed(hand, 0)
    clone.seed(hand, 0)
    assert bot.run([], state) == clone.run([], state)
    assert bot.random_state == clone.random_state


def test_river_sizes_for_value_against_station():
    from river_policy import choose_river_bet
    bet = choose_river_bet(
        encoded('AS AH'), encoded('AC 7D 8C 2H 3S'),
        ([tuple(encoded('KC KD'))], [1.0]),
        pot=100, min_bet=20, max_bet=200, fold_rate=0.02,
        aggression=0.05, big_blind=20,
    )
    assert bet == 200


def test_river_does_not_bluff_station_with_losing_hand():
    from river_policy import choose_river_bet
    bet = choose_river_bet(
        encoded('4S 5H'), encoded('AC 7D 8C 2H KS'),
        ([tuple(encoded('KC KD'))], [1.0]),
        pot=100, min_bet=20, max_bet=200, fold_rate=0.02,
        aggression=0.05, big_blind=20,
    )
    assert bet == 0


def test_river_checks_unbeatable_shared_board():
    from river_policy import choose_river_bet
    bet = choose_river_bet(
        encoded('2C 3D'), encoded('AS KS QS JS TS'),
        ([tuple(encoded('4C 5D'))], [1.0]),
        pot=100, min_bet=20, max_bet=200, fold_rate=0.8,
        aggression=0.2, big_blind=20,
    )
    assert bet == 0


def test_river_cannot_bet_above_effective_stack():
    from poker_math import all_hands
    from river_policy import choose_river_bet
    hand, board = encoded('AS AH'), encoded('AC 7D 8C 2H 3S')
    hands = all_hands(set(hand) | set(board))
    bet = choose_river_bet(hand, board, (hands, [1.0] * len(hands)),
                           100, 20, 57, 0.1, 0.1, 20)
    assert 0 <= bet <= 57
    assert bet == 0 or bet >= 20


def test_preflop_folding_stats_exclude_postflop_folds():
    bot = Model()
    bot.seed(cards('AS AH'), 0)
    state = GameState([500, 500], teams=['us', 'villain'])
    bot._prepare(GameStateView(state))
    bot.seen_board = encoded('2C 3D 7H')
    bot.tracked_bets = [40, 0]
    bot._observe([PlayerAction.fold(1)], GameStateView(state))
    stats = bot.opponents['villain']
    assert stats['folds'] == 1
    assert stats['pre_folds'] == 0


@pytest.mark.parametrize('hole,board,expected', [
    ('AS QD', '6C 7D 8H 9S', 0.0),
    ('8H TS', '6C 7D QH', 0.09),
    ('AH 2D', '3C 4S 9H', 0.09),
])
def test_straight_draw_needs_private_card_contribution(hole, board, expected):
    from poker_math import draw_strength
    assert draw_strength(encoded(hole), encoded(board)) == pytest.approx(expected)


def test_river_values_short_opponent_with_legal_minimum_raise():
    state = GameState([500, 25])
    # Both players limp, then check through flop and turn.
    state.process_action(PlayerAction.call(0))
    state.process_action(PlayerAction.call(1))
    board = cards('AC 7D 8C 2H 3S')
    for card in board[:3]:
        state.deal_card(card)
    for next_card in board[3:]:
        state.process_action(PlayerAction.call(1))
        state.process_action(PlayerAction.call(0))
        state.deal_card(next_card)
    state.process_action(PlayerAction.call(1))
    assert state.stacks[1] == 5
    bot = Model()
    bot.seed(cards('AS AH'), 0)
    view = GameStateView(state)
    bot._prepare(view)
    bot.ranges[1] = ([tuple(encoded('KC KD'))], [1.0])
    action = bot._decide(view, [1], encoded('AC 7D 8C 2H 3S'), 1.0, random.Random(1))
    assert action.kind == 'raise'
    assert action.amount == state.min_raise_to == 20
    state.validate_action(action)
