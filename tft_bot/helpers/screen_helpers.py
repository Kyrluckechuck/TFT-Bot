"""A collection of screen helpers for detecting when images are on screen."""
import cv2
from loguru import logger
import mss
import numpy
import win32gui

from tft_bot.constants import CONSTANTS
from tft_bot.helpers.system_helpers import resource_path


def get_window_bounding_box(window_title: str) -> tuple[int, int, int, int] | None:
    """
    Gets the bounding box of a specific window.

    Returns:
        A tuple of coordinates (top left x and y and bottom right x and y) or None if no window exists.

    """
    league_game_window_handle = win32gui.FindWindowEx(0, 0, 0, window_title)
    if not league_game_window_handle:
        logger.debug(f"We tried to check {window_title} for an image, but there is no window")
        return None

    return win32gui.GetWindowRect(league_game_window_handle)


def check_league_game_size() -> None:
    """
    Check the league game size and print an error if it is not what we need it to be.
    """
    league_game_bounding_box = get_window_bounding_box(window_title="League of Legends (TM) Client")
    if not league_game_bounding_box:
        return

    top_left_x, top_left_y, bottom_right_x, bottom_right_y = league_game_bounding_box
    if bottom_right_x - top_left_x != 1920 or bottom_right_y - top_left_y != 1080:
        logger.error(
            f"Your game's size is {bottom_right_x - top_left_x} x {bottom_right_y - top_left_y} "
            f"instead of 1920 x 1080! This WILL cause issues!"
        )


def get_on_screen_in_client(
    path: str, precision: float = 0.8, offsets: tuple[int, int, int, int] | None = None
) -> tuple[int, int, int, int] | None:
    """
    Check if a given image is detected on screen, but only check the league client window.

    Args:
        path: The relative or absolute path to the image to be found.
        precision: The precision to be used when matching the image. Defaults to 0.8.
        offsets: A tuple of coordinates to off-set the region by. Useful if you only want to check a specific region.
          All offsets are from the top-left of the game window.

    Returns:
        The position of the image and it's width and height or None if it wasn't found
    """
    return get_on_screen(
        window_title=CONSTANTS["window_titles"]["client"], path=path, precision=precision, offsets=offsets
    )


def get_on_screen_in_game(
    path: str, precision: float = 0.8, offsets: tuple[int, int, int, int] | None = None
) -> tuple[int, int, int, int] | None:
    """
    Check if a given image is detected on screen, but only check the league game window.

    Args:
        path: The relative or absolute path to the image to be found.
        precision: The precision to be used when matching the image. Defaults to 0.8.
        offsets: A tuple of coordinates to off-set the region by. Useful if you only want to check a specific region.
          All offsets are from the top-left of the game window.

    Returns:
        The position of the image and it's width and height or None if it wasn't found
    """
    return get_on_screen(
        window_title=CONSTANTS["window_titles"]["game"], path=path, precision=precision, offsets=offsets
    )


def get_on_screen(
    window_title: str, path: str, precision: float = 0.8, offsets: tuple[int, int, int, int] | None = None
) -> tuple[int, int, int, int] | None:
    """
    Check if a given image is detected on screen in a specific window's area.

    Args:
        window_title: The title of the window we should look at.
        path: The relative or absolute path to the image to be found.
        precision: The precision to be used when matching the image. Defaults to 0.8.
        offsets: A tuple of coordinates to off-set the region by. Useful if you only want to check a specific region.
          All offsets are from the top-left of the game window.

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
        new_bounding_box = ()
        for i in range(4):
            new_bounding_box += (window_bounding_box[i % 2] + offsets[i],)
        window_bounding_box = new_bounding_box

    with mss.mss() as screenshot_taker:
        screenshot = screenshot_taker.grab(tuple(window_bounding_box))

    pixels = numpy.array(screenshot)
    gray_scaled_pixels = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
    search_result = cv2.matchTemplate(gray_scaled_pixels, image_to_find, cv2.TM_CCOEFF_NORMED)

    _, max_precision, _, max_location = cv2.minMaxLoc(search_result)
    if max_precision < precision:
        return None

    return max_location + (image_to_find.shape[0], image_to_find.shape[1])


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
