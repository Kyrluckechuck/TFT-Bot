import logging
import time

import python_imagesearch.imagesearch as imagesearch

from system_helpers import resource_path


def onscreen(path, precision=0.8) -> bool:
    path = resource_path(path)
    try:
        return imagesearch.imagesearch(path, precision)[0] != -1
    except Exception:
        return False

def onscreen_multiple_any(paths, precision=0.8) -> bool:
    try:
        for path in paths:
            path = resource_path(path)
            is_onscreen = imagesearch.imagesearch(path, precision)[0]
            # logging.debug(f"is_onscreen: {is_onscreen != -1}") #Advanced debugging not even normally needed
            if is_onscreen != -1:
                return True
    except Exception as err:
        logging.debug(f"multiple_onscreen_any error: {err}")

    return False

def onscreen_region(path, x1, y1, x2, y2, precision=0.8) -> (bool | list[int] | tuple[int, int]): # pylint: disable=invalid-name
    try:
        path = resource_path(path)
        pos = imagesearch.imagesearcharea(path, x1, y1, x2, y2, precision)
        return pos if pos[0] != -1 else False
    except Exception:
        return False

def onscreen_region_numLoop(path, timesample, maxSamples, x1, y1, x2, y2, precision=0.8) -> (bool | list[int] | tuple[int, int]): # pylint: disable=invalid-name
    try:
        path = resource_path(path)
        return imagesearch_region_numLoop(path, timesample, maxSamples, x1, y1, x2, y2, precision)[0] != -1
    except Exception:
        return False

# Via https://github.com/drov0/python-imagesearch/blob/master/python_imagesearch/imagesearch.py
def imagesearch_region_numLoop(image, timesample, maxSamples, x1, y1, x2, y2, precision=0.8) -> (None | list[int] | tuple[int, int]): # pylint: disable=invalid-name
    try:
        image = resource_path(image)
        pos = imagesearch.imagesearcharea(image, x1, y1, x2, y2, precision)
        count = 0

        while pos[0] == -1:
            time.sleep(timesample)
            pos = imagesearch.imagesearcharea(image, x1, y1, x2, y2, precision)
            count = count + 1
            if count > maxSamples:
                break
        return pos
    except Exception:
        return None

def find_image(path, precision=0.8) -> (None | list[int] | tuple[int, int]):
    try:
        path = resource_path(path)
        pos = imagesearch.imagesearch(path, precision)
        return pos if pos[0] != -1 else None
    except Exception:
        return None

def find_image_multiple_any(paths, precision=0.8) -> (None | list[int] | tuple[int, int]):
    try:
        for path in paths:
            path = resource_path(path)
            pos = imagesearch.imagesearch(path, precision)
            # logging.debug(f"is_onscreen: {pos[0] != -1}") #Advanced debugging not even normally needed
            if pos[0] != -1:
                return pos
            else:
                return None
    except Exception as err:
        logging.debug(f"multiple_onscreen_any error: {err}")

    return None

def find_image_in_region_numLoop(path, timesample, maxSamples, x1, y1, x2, y2, precision=0.8) -> (None | list[int] | tuple[int, int]): # pylint: disable=invalid-name
    try:
        path = resource_path(path)
        pos = imagesearch_region_numLoop(path, timesample, maxSamples, x1, y1, x2, y2, precision)
        return pos if pos[0] != -1 else None
    except Exception:
        return None
