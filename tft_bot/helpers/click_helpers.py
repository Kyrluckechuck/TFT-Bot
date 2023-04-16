"""A collection of click helpers."""
import random
import time

import pyautogui as auto

from tft_bot.helpers.screen_helpers import ImageSearchResult


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


def click_to(
    position_x: int,
    position_y: int,
    move_duration: float = random.uniform(0.1, 1.0),
    delay: float = 0.2,
    action: str = "left",
) -> None:
    """
    Click to a specific position on the screen

    Args:
        position_x: The x coordinate to click to
        position_y: The y coordinate to click to
        move_duration (float, optional): Time taken for the mouse to move.
            Defaults to random.uniform(0.1, 1.0).
        delay (float, optional): The delay between mouse down & up. Defaults to 0.2.
        action (str, optional): The mouse button to perform. Defaults to "left".
    """
    auto.moveTo(position_x, position_y, move_duration)
    mouse_button(delay=delay, button=action)


def click_to_image(
    image_search_result: ImageSearchResult | None,
    move_duration: float = random.uniform(0.1, 1.0),
    delay: float = 0.2,
    action: str = "left",
    middle: bool = True,
) -> bool:
    """
    Attempt to click to a specified image.

    Args:
        image_search_result: The result of an image search (screen_helpers.get_on_screen)
        move_duration: Time taken for the mouse to move.
            Defaults to random.uniform(0.1, 1.0).
        delay: The delay between mouse down & up. Defaults to 0.2.
        action: The mouse button to perform. Defaults to "left".
        middle: Whether to click to the approximate middle of the image. Defaults to True.

    Returns:
        True if we had an image to click to, False if not
    """
    if not image_search_result:
        return False

    offset_x = 0
    offset_y = 0

    if middle:
        offset_x = image_search_result.width / 2
        offset_y = image_search_result.height / 2

    click_to(
        position_x=image_search_result.position_x + offset_x,
        position_y=image_search_result.position_y + offset_y,
        move_duration=move_duration,
        delay=delay,
        action=action,
    )
    return True
