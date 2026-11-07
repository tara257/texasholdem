"""Local robustness opponents. Not imported by, or shipped with, our bot.

These intentionally change policy under a stable team name so an opponent
cannot rely on one lifetime-average description of their behaviour.
"""
from arena.dummies import CallBot, FoldBot, ShoveBot, TightBot


class SwitchingAggression:
    def __init__(self):
        self.passive = FoldBot()
        self.aggressive = ShoveBot()
        self.hands = 0
        self.phase = False

    def seed(self, hand, player_id):
        self.phase = (self.hands // 40) % 2 == 1
        self.hands += 1
        self.passive.seed(hand, player_id)
        self.aggressive.seed(hand, player_id)

    def run(self, actions, state):
        bot = self.aggressive if self.phase else self.passive
        return bot.run(actions, state)


class SwitchingCalling:
    def __init__(self):
        self.caller = CallBot()
        self.tight = TightBot()
        self.hands = 0
        self.phase = False

    def seed(self, hand, player_id):
        self.phase = (self.hands // 40) % 2 == 1
        self.hands += 1
        self.caller.seed(hand, player_id)
        self.tight.seed(hand, player_id)

    def run(self, actions, state):
        bot = self.tight if self.phase else self.caller
        return bot.run(actions, state)
