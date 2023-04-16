"""A collection of click helpers."""
import random
import time
from typing import Callable

from loguru import logger
import pyautogui as auto

from . import generic_helpers
from .better_image_click import click_image_rand
from .screen_helpers import find_image
from .system_helpers import resource_path


def mouse_button(delay=0.1, button="left") -> None:
    """A click helper to simulate clicking the specified button.

    Args:
        delay (float, optional): The delay between button down & up. Defaults to .1.
        button (str, optional): Button of the mouse to activate : "left" "right" "middle",
            see pyautogui.click documentation for more info. Defaults to "left".
    """
    auto.mouseDown(button=button)
    time.sleep(delay)
    auto.mouseUp(button=button)


def click_key(key: str, delay: float = 0.1) -> None:
    """Simulate a click on the specified key.

    Args:
        key (str): The key to click.
        delay (float, optional): The delay between key down and key up events. Defaults to .1.
    """
    auto.keyDown(key)
    time.sleep(delay)
    auto.keyUp(key)


def click_left(delay=0.1) -> None:
    """Simulate a click on the left mouse button.

    Args:
        delay (float, optional): The delay between key down and key up events. Defaults to .1.
    """
    mouse_button(delay=delay, button="left")


def click_right(delay=0.1) -> None:
    """Simulate a click on the right mouse button.

    Args:
        delay (float, optional): The delay between key down and key up events. Defaults to .1.
    """
    mouse_button(delay=delay, button="right")


def click_to_middle(  # pylint: disable=too-many-arguments
    path: str,
    precision: float = 0.8,
    move_duration: float = random.uniform(0.1, 1.0),
    delay: float = 0.2,
    offset: float | str = "half",
    action: str = "left",
) -> bool:
    """Attempt to click to the (relative) middle of the specified image.

    Args:
        path (str): The relative or absolute path to the image to be clicked.
        precision (float, optional): The precision to be used when matching the image.
            Defaults to 0.8.
        move_duration (float, optional): Time taken for the mouse to move.
            Defaults to random.uniform(0.1, 1.0).
        delay (float, optional): The delay between mouse down & up. Defaults to 0.2.
        offset (float | str, optional): When specified, the manual offset from the relative center in pixels.
            Defaults to "half".
        action (str, optional): The mouse button to perform. Defaults to "left".

    Returns:
        bool: True if successfully clicked, False otherwise.
    """
    path = resource_path(path)
    pos = find_image(path, precision)
    if pos:
        try:
            return click_image_rand(
                path,
                pos,
                action,
                move_duration=move_duration,
                delay=delay,
                offset=offset,
            )
        except Exception as err:
            logger.debug(f"M|Failed to click to {err}")
    else:
        logger.debug(f"M|Could not find '{path}', skipping")
    return False


def click_to_middle_multiple(
    images: list[str],
    precision: float = 0.8,
    conditional_func: Callable | None = None,
    delay: float = None,
    action: str = "left",
) -> bool:
    """Attempt to click to the (relative) middle of the specified images.

    Args:
        images (list[str]): The list of relative or absolute paths to images to attempt clicking.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.
        conditional_func (Callable | None, optional): The function to evaluate if the click was successful.
            Defaults to None.
        delay (float, optional): The delay between mouse down & up. Defaults to None.
        action (str, optional): The mouse button to perform. Defaults to "left".

    Returns:
        bool: _description_
    """
    for image in images:
        image = resource_path(image)
        try:
            click_to_middle(image, precision=precision, action=action)
        except Exception:
            logger.debug(f"M|Failed to click {image}")
        if generic_helpers.is_var_number(delay):
            time.sleep(delay)
        if generic_helpers.is_var_function(conditional_func) and conditional_func():
            return True
    return False
