"""A collection of click helpers."""
import random
import time

import pyautogui as auto


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


def click_to_middle(
    image_details: tuple[int, int, int, int],
    move_duration: float = random.uniform(0.1, 1.0),
    delay: float = 0.2,
    action: str = "left",
) -> None:
    """Attempt to click to the (relative) middle of the specified image.

    Args:
        image_details: The coordinates to click to, and the height and width
        move_duration (float, optional): Time taken for the mouse to move.
            Defaults to random.uniform(0.1, 1.0).
        delay (float, optional): The delay between mouse down & up. Defaults to 0.2.
        action (str, optional): The mouse button to perform. Defaults to "left".
    """
    auto.moveTo(
        image_details[0] + image_details[2] / 2,
        image_details[1] + image_details[3] / 2,
        move_duration,
    )
    mouse_button(delay=delay, button=action)
