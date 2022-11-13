import logging
import random
import time

import cv2
import pyautogui as auto


def click_image_rand(image, pos, action, move_duration, offset="half", delay=0.1) -> bool:
    img = cv2.imread(image)
    if img is None:
        logging.debug(f'Image file not found: {image}')
        return False
    height, width, _channel = img.shape
    offset_to_use = min(height, width) / 2
    if offset != "half":
        offset_to_use = offset
    auto.moveTo(pos[0] + rand_func(width / 2, offset_to_use), pos[1] + rand_func(height / 2, offset_to_use), move_duration)
    click_action(delay=delay, button=action)
    return True

def click_action(delay=.1, button="left") -> None:
    auto.mouseDown(button=button)
    time.sleep(delay)
    auto.mouseUp(button=button)

def rand_func(num, rand) -> float:
    return num + rand * random.random()
