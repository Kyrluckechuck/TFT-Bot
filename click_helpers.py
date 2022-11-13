import logging
import random
import time

import pyautogui as auto
import python_imagesearch.imagesearch as imagesearch

import generic_helpers
from better_image_click import click_image_rand
from screen_helpers import find_image, onscreen
from system_helpers import resource_path


def click_key(key, delay=.1) -> None:
    auto.keyDown(key)
    time.sleep(delay)
    auto.keyUp(key)


def click_left(delay=.1) -> None:
    auto.mouseDown()
    time.sleep(delay)
    auto.mouseUp()


def click_right(delay=.1) -> None:
    auto.mouseDown(button='right')
    time.sleep(delay)
    auto.mouseUp(button='right')


def click_to(path, precision=0.8, delay=.1) -> None:
    path = resource_path(path)
    if onscreen(path, precision):
        try:
            auto.moveTo(imagesearch.imagesearch(path))
            click_left(delay)
        except Exception as err:
            logging.debug(f"Failed to click to {err}")
    else:
        logging.debug(f"Could not find '{path}', skipping")

def click_to_multiple(images, conditional_func=None, delay=None) -> bool:
    for image in images:
        image = resource_path(image)
        try:
            click_to(image)
        except Exception:
            logging.debug(f"Failed to click {image}")
        if generic_helpers.is_var_number(delay):
            time.sleep(delay)
        if generic_helpers.is_var_function(conditional_func) and conditional_func():
            return True
    return False

def search_to(path) -> (None | list[int] | tuple[int, int]):
    try:
        path = resource_path(path)
        pos = imagesearch.imagesearch(path)
        if onscreen(path):
            auto.moveTo(pos)
            return pos
    except Exception:
        return None

def click_to_middle(path, precision=0.8, move_duration=random.uniform(0.1, 1.0), delay=0.2, offset="half", action="left") -> bool:
    path = resource_path(path)
    pos = find_image(path, precision)
    if pos:
        try:
            return click_image_rand(path, pos, action, move_duration=move_duration, delay=delay, offset=offset)
        except Exception as err:
            logging.debug(f"M|Failed to click to {err}")
    else:
        logging.debug(f"M|Could not find '{path}', skipping")
    return False

def click_to_middle_multiple(images, precision=0.8, conditional_func=None, delay=None, action="left") -> bool:
    for image in images:
        image = resource_path(image)
        try:
            click_to_middle(image, precision=precision, action=action)
        except Exception:
            logging.debug(f"M|Failed to click {image}")
        if generic_helpers.is_var_number(delay):
            time.sleep(delay)
        if generic_helpers.is_var_function(conditional_func) and conditional_func():
            return True
    return False
