"""
Module holding the default economy mode.
"""
import time

from ..helpers import screen_helpers
from .base import EconomyMode


class DefaultEconomyMode(EconomyMode):
    """
    Default economy mode implementation.
    """

    def loop_decision(self, minimum_round: int):
        if screen_helpers.gold_at_least(3):
            self.purchase_units(amount=3)
            time.sleep(0.5)

        if minimum_round < 3:
            return

        if screen_helpers.gold_at_least(4):
            self.purchase_xp()
            time.sleep(0.5)

        if screen_helpers.gold_at_least(5):
            self.roll()
            time.sleep(0.5)
