"""A collection of screen helpers for detecting when images are on screen."""
from dataclasses import dataclass

import cv2
from loguru import logger
import mss
import numpy
from pytesseract import pytesseract
import win32gui

from tft_bot.constants import CONSTANTS
from tft_bot.helpers.system_helpers import resource_path


@dataclass
class BoundingBox:
    """
    A dataclass holding information about a bounding box, a rectangle of two coordinate sets.
    """

    min_x: int
    min_y: int
    max_x: int
    max_y: int

    def to_tuple(self) -> tuple[int, int, int, int]:
        """
        Converts the bounding box to a tuple.

        Returns:
            A tuple, ordered min_x, min_y, max_x, max_y.

        """
        return self.min_x, self.min_y, self.max_x, self.max_y

    def get_width(self) -> int:
        """
        Get the width of the bounding box.

        Returns:
            The width as an integer.
        """
        return self.max_x - self.min_x

    def get_height(self) -> int:
        """
        Get the height of the bounding box.

        Returns:
            The height as an integer.
        """
        return self.max_y - self.min_y


@dataclass
class Coordinates:
    """
    A dataclass holding information about offset pixels to click to.
    """

    position_x: int
    position_y: int


@dataclass
class ImageSearchResult(Coordinates):
    """
    A dataclass holding information about an image search result.
    """

    width: int
    height: int


def get_window_bounding_box(window_title: str) -> BoundingBox | None:
    """
    Gets the bounding box of a specific window.

    Returns:
        A bounding box (min x, min y, max x, max y) or None if no window exists.

    """
    league_game_window_handle = win32gui.FindWindowEx(0, 0, 0, window_title)
    if not league_game_window_handle:
        logger.debug(f"We tried to check {window_title} for an image, but there is no window")
        return None

    return BoundingBox(*win32gui.GetWindowRect(league_game_window_handle))


def check_league_game_size() -> None:
    """
    Check the league game size and print an error if it is not what we need it to be.
    """
    league_game_bounding_box = get_window_bounding_box(window_title="League of Legends (TM) Client")
    if not league_game_bounding_box:
        return

    if league_game_bounding_box.get_width() != 1920 or league_game_bounding_box.get_height() != 1080:
        logger.error(
            f"Your game's size is {league_game_bounding_box.get_width()} x {league_game_bounding_box.get_height()} "
            f"instead of 1920 x 1080! This WILL cause issues!"
        )


def calculate_window_click_offset(window_title: str, position_x: int, position_y: int) -> Coordinates | None:
    """
    Calculate absolute screen coordinates based off relative pixel position in a specific window.

    Args:
        window_title: The title of the window to click in.
        position_x: The relative x coordinate to click to.
        position_y: The relative y coordinate to click to.

    Returns:
        Absolute coordinates to click to.
    """
    window_bounding_box = get_window_bounding_box(window_title=window_title)
    if not window_bounding_box:
        return None

    return Coordinates(
        position_x=window_bounding_box.min_x + position_x, position_y=window_bounding_box.min_y + position_y
    )


def get_on_screen_in_client(
    path: str, precision: float = 0.8, offsets: BoundingBox | None = None
) -> ImageSearchResult | None:
    """
    Check if a given image is detected on screen, but only check the league client window.

    Args:
        path: The relative or absolute path to the image to be found.
        precision: The precision to be used when matching the image. Defaults to 0.8.
        offsets: A bounding box to off-set the region by. Useful if you only want to check a specific region.
          Defaults to None.

    Returns:
        The position of the image and it's width and height or None if it wasn't found
    """
    return get_on_screen(
        window_title=CONSTANTS["window_titles"]["client"], path=path, precision=precision, offsets=offsets
    )


def get_on_screen_in_game(
    path: str, precision: float = 0.8, offsets: BoundingBox | None = None
) -> ImageSearchResult | None:
    """
    Check if a given image is detected on screen, but only check the league game window.

    Args:
        path: The relative or absolute path to the image to be found.
        precision: The precision to be used when matching the image. Defaults to 0.8.
        offsets: A bounding box to off-set the region by. Useful if you only want to check a specific region.
          Defaults to None.

    Returns:
        The position of the image and it's width and height or None if it wasn't found
    """
    return get_on_screen(
        window_title=CONSTANTS["window_titles"]["game"], path=path, precision=precision, offsets=offsets
    )


def get_on_screen(
    window_title: str, path: str, precision: float = 0.8, offsets: BoundingBox | None = None
) -> ImageSearchResult | None:
    """
    Check if a given image is detected on screen in a specific window's area.

    Args:
        window_title: The title of the window we should look at.
        path: The relative or absolute path to the image to be found.
        precision: The precision to be used when matching the image. Defaults to 0.8.
        offsets: A bounding box to off-set the region by. Useful if you only want to check a specific region.
          Defaults to None.

    Returns:
        The position of the image and it's width and height or None if it wasn't found
    """
    window_bounding_box = get_window_bounding_box(window_title=window_title)
    if not window_bounding_box:
        return None

    image_to_find = cv2.imread(path, 0)
    if image_to_find is None:
        logger.warning(f"The image {path} does not exist on the system or we do not have permission to read it")
        return None

    if offsets:
        window_bounding_box.min_x += offsets.min_x
        window_bounding_box.min_y += offsets.min_y
        window_bounding_box.max_x += offsets.max_x
        window_bounding_box.max_y += offsets.max_y

    with mss.mss() as screenshot_taker:
        screenshot = screenshot_taker.grab(window_bounding_box.to_tuple())

    pixels = numpy.array(screenshot)
    gray_scaled_pixels = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
    search_result = cv2.matchTemplate(gray_scaled_pixels, image_to_find, cv2.TM_CCOEFF_NORMED)

    _, max_precision, _, max_location = cv2.minMaxLoc(search_result)
    if max_precision < precision:
        return None

    return ImageSearchResult(
        position_x=max_location[0] + window_bounding_box.min_x,
        position_y=max_location[1] + window_bounding_box.min_y,
        height=image_to_find.shape[0],
        width=image_to_find.shape[1],
    )


@logger.catch
def get_on_screen_multiple_any(window_title: str, paths: list[str], precision: float = 0.8) -> bool:
    """Check if any of the given images are detected on screen.

    Args:
        window_title: The title of the window we should look at.
        paths: The list of relative or absolute paths to images to be searched for.
        precision: The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        True if any of the images are detected on screen, False otherwise.
    """
    for path in paths:
        if get_on_screen(window_title=window_title, path=resource_path(path), precision=precision):
            return True

    return False


_TESSERACT_CONFIG = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789 -c page_separator=""'


def get_gold_with_ocr() -> int:
    """
    Get the gold by taking a screenshot of the region where it is and running OCR over it.
    This should only be called by ocr_* implementations in the economy package, since they set where Tesseract-OCR is.

    Returns:
        The amount of gold the player currently has.

    """
    league_bounding_box = get_window_bounding_box(CONSTANTS["window_titles"]["game"])
    if not league_bounding_box:
        return 0

    gold_bounding_box = (
        league_bounding_box.min_x + 867,
        league_bounding_box.min_y + 881,
        league_bounding_box.min_x + 924,
        league_bounding_box.min_y + 909,
    )
    with mss.mss() as screenshot_taker:
        screenshot = screenshot_taker.grab(gold_bounding_box)

    pixels = numpy.array(screenshot)
    gray_scaled_pixels = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
    return int(pytesseract.image_to_string(~gray_scaled_pixels, config=_TESSERACT_CONFIG) or 0)


def get_gold_with_opencv(num: int) -> bool:
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
    Check if the gold on screen is at least the provided amount with opencv

    Args:
        num (int): The value to check if the gold is at least.

    Returns:
        bool: True if the value is >= `num`, False otherwise.
    """
    logger.debug(f"Looking for at least {num} gold")
    if get_gold_with_opencv(num):
        return True

    for i in range(num + 1):
        if get_gold_with_opencv(i):
            return i >= num

    logger.debug("No gold value found, assuming we have more")
    return True
