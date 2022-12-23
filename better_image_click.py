"""A 'better' center-of-image clicking implementation."""
import logging
import time

import cv2
import pyautogui as auto

from generic_helpers import rand_func


def click_image_rand(image, pos, action, move_duration, offset="half", delay=0.1) -> bool:  # pylint: disable=too-many-arguments
    """
    Explanation from https://github.com/drov0/python-imagesearch/blob/master/python_imagesearch/imagesearch.py
    click on the center of an image with a bit of random.
    eg, if an image is 100*100 with an offset of 5 it may click at 52,50 the first time and then 55,53 etc
    Usefull to avoid anti-bot monitoring while staying precise.
    this function doesn't search for the image, it's only ment for easy clicking on the images.

    Args:
        image: Path to the image file (see opencv imread for supported types).
        pos: Array containing the position of the top left corner of the image [x,y].
        action: Button of the mouse to activate : "left" "right" "middle", see pyautogui.click documentation for more info.
        move_duration: Time taken for the mouse to move from where it was to the new position.
        offset (str, optional): When specified, the manual offset from the relative center in pixels. Defaults to "half".
        delay (float, optional): The delay between mouse down & up. Defaults to 0.1.

    Returns:
        bool: True if image found, False otherwise.
    """
    img = cv2.imread(image)
    if img is None:
        logging.debug(f"Image file not found: {image}")
        return False
    height, width, _channel = img.shape
    offset_to_use = min(height, width) / 2
    if offset != "half":
        offset_to_use = offset
    auto.moveTo(
        pos[0] + rand_func(width / 2, offset_to_use),
        pos[1] + rand_func(height / 2, offset_to_use),
        move_duration,
    )
    mouse_button(delay=delay, button=action)
    return True


def mouse_button(delay=0.1, button="left") -> None:
    """A click helper to simulate clicking the specified button.
    *NOTE* Copied from `click_helpers` to avoid a cyclical import

    Args:
        delay (float, optional): The delay between button down & up. Defaults to .1.
        button (str, optional): Button of the mouse to activate : "left" "right" "middle", see pyautogui.click documentation for more info. Defaults to "left".
    """
    auto.mouseDown(button=button)
    time.sleep(delay)
    auto.mouseUp(button=button)
