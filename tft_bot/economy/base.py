"""
Module holding the base economy mode blueprint class.
"""
import time

from tft_bot.constants import CONSTANTS
from tft_bot.helpers.click_helpers import click_to_image
from tft_bot.helpers.screen_helpers import get_on_screen_in_game


class EconomyMode:
    """
    Blueprint class to implement custom economy modes on.
    """

    def __init__(self, wanted_traits: list[str], prioritized_order: bool):
        """
        Init method to dependency-inject the purchase logic.
        Args:
            wanted_traits: A list of wanted traits.
            prioritized_order: Whether to only buy a trait if the trait before it was bought.
        """
        self.wanted_traits = wanted_traits
        self.prioritized_order = prioritized_order

    def loop_decision(self, minimum_round: int) -> None:
        """
        Method to be called by the main game loop for the mode to make a decision.

        Args:
            minimum_round: The n-th round (N-*) we are at.
        """
        raise NotImplementedError

    def purchase_units(self, amount: int) -> None:
        """
        Attempts to purchase a given amount of units from the pool of configured traits.

        Args:
            amount: The amount of units to purchase.
        """
        for _ in range(amount):
            for trait in self.wanted_traits:
                if click_to_image(image_search_result=get_on_screen_in_game(CONSTANTS["game"]["trait"][trait])):
                    time.sleep(0.5)
                elif self.prioritized_order:
                    return

    def roll(self) -> None:
        """
        Utility method to roll (refresh) the shop once.
        """
        click_to_image(image_search_result=get_on_screen_in_game(CONSTANTS["game"]["gamelogic"]["reroll"]))

    def purchase_xp(self) -> None:
        """
        Utility method to purchase xp once.
        """
        click_to_image(image_search_result=get_on_screen_in_game(CONSTANTS["game"]["gamelogic"]["xp_buy"]))
