"""
Module holding the OCR standard economy mode.
"""
from loguru import logger
from pytesseract import pytesseract

from tft import GAME_CLIENT_INTEGRATION

from ..helpers import screen_helpers
from .base import EconomyMode


class OCRStandardEconomyMode(EconomyMode):
    """
    OCR standard economy mode implementation.
    """

    def __init__(self, wanted_traits: list[str], prioritized_order: bool, tesseract_location: str):
        super().__init__(wanted_traits, prioritized_order)
        pytesseract.tesseract_cmd = tesseract_location

    def loop_decision(self, minimum_round: int):
        self.purchase_units(amount=3)

        gold = screen_helpers.get_gold_with_ocr()
        logger.debug(f"OCR recognized {gold} gold")
        if gold >= 54 and GAME_CLIENT_INTEGRATION.get_level() < 8:
            self.purchase_xp()
            gold -= 4

        if gold >= 55:
            self.roll()
