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


def click_to(
    position: tuple[int, int],
    move_duration: float = random.uniform(0.1, 1.0),
    delay: float = 0.2,
    action: str = "left",
) -> None:
    """
    Click to a specific position on the screen

    Args:
        position: The coordinates to click to
        move_duration (float, optional): Time taken for the mouse to move.
            Defaults to random.uniform(0.1, 1.0).
        delay (float, optional): The delay between mouse down & up. Defaults to 0.2.
        action (str, optional): The mouse button to perform. Defaults to "left".
    """
    auto.moveTo(position[0], position[1], move_duration)
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
        position=(image_search_result.position_x + offset_x, image_search_result.position_y + offset_y),
        move_duration=move_duration,
        delay=delay,
        action=action,
    )
    return True
