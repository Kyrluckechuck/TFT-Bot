"""
Module holding the default economy mode.
"""
import time

from loguru import logger

from ..constants import CONSTANTS
from ..helpers.screen_helpers import BoundingBox
from ..helpers.screen_helpers import get_on_screen_in_game
from .base import EconomyMode


class DefaultEconomyMode(EconomyMode):
    """
    Default economy mode implementation.
    """

    def loop_decision(self, minimum_round: int):
        if gold_at_least(3):
            self.purchase_units(amount=3)
            time.sleep(0.5)

        if minimum_round < 3:
            return

        if gold_at_least(4):
            self.purchase_xp()
            time.sleep(0.5)

        if gold_at_least(5):
            self.roll()
            time.sleep(0.5)


def get_gold(num: int) -> bool:
    """
    Checks if there is N gold in the region of the gold display.

    Args:
        num: The amount of gold we're checking for, there should be a file for it in captures/gold .

    Returns:
        True if we found the amount of gold. False if not.
    """
    try:
        if get_on_screen_in_game(CONSTANTS["game"]["gold"][f"{num}"], 0.9, BoundingBox(780, 850, 970, 920)):
            logger.debug(f"Found {num} gold")
            return True
    except Exception as exc:
        logger.opt(exception=exc).debug(f"Exception finding {num} gold, we possibly don't have the value as a file")
        # We don't have this gold as a file
        return True
    return False


def gold_at_least(num: int) -> bool:
    """
    Check if the gold on screen is at least the provided amount

    Args:
        num (int): The value to check if the gold is at least.

    Returns:
        bool: True if the value is >= `num`, False otherwise.
    """
    logger.debug(f"Looking for at least {num} gold")
    if get_gold(num):
        return True

    for i in range(num + 1):
        if get_gold(i):
            return i >= num

    logger.debug("No gold value found, assuming we have more")
    return True
