"""
Module holding the OCR standard economy mode.
"""
import cv2
import mss
import numpy
from pytesseract import pytesseract

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

        gold = get_gold()
        if gold >= 54:
            self.purchase_xp()
            gold -= 4

        if gold >= 55:
            self.roll()


_TESSERACT_CONFIG = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789 -c page_separator=""'


def get_gold() -> int:
    """
    Get the gold by taking a screenshot of the region where it is and running OCR over it.

    Returns:
        The amount of gold the player currently has.

    """
    with mss.mss() as screenshot_taker:
        screenshot = screenshot_taker.grab((867, 881, 924, 909))

    pixels = numpy.array(screenshot)
    gray_scaled_pixels = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
    return int(pytesseract.image_to_string(~gray_scaled_pixels, config=_TESSERACT_CONFIG) or 0)
