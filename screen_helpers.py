"""A collection of screen helpers for detecting when images are on screen."""
import time

from loguru import logger
from python_imagesearch import imagesearch

from system_helpers import resource_path


def onscreen(path: str, precision: float = 0.8) -> bool:
    """Check if a given image is detected on screen.

    Args:
        path (str): The relative or absolute path to the image to be found.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        bool: True if the image is detected on screen, False otherwise.
    """
    path = resource_path(path)
    try:
        return imagesearch.imagesearch(path, precision)[0] != -1
    except Exception:
        return False


def onscreen_multiple_any(paths: list[str], precision: float = 0.8) -> bool:
    """Check if any of the given images are detected on screen.

    Args:
        paths (list[str]): The list of relative or absolute paths to images to be searched for.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        bool: True if any of the images are detected on screen, False otherwise.
    """
    try:
        for path in paths:
            path = resource_path(path)
            is_onscreen = imagesearch.imagesearch(path, precision)[0]
            # logger.debug(f"is_onscreen: {is_onscreen != -1}") #Advanced debugging not even normally needed
            if is_onscreen != -1:
                return True
    except Exception as err:
        logger.debug(f"multiple_onscreen_any error: {err}")

    return False


def onscreen_region(  # pylint: disable=invalid-name,too-many-arguments,disable=invalid-name
    path: str, x1: int, y1: int, x2: int, y2: int, precision: float = 0.8
) -> bool | list[int] | tuple[int, int]:
    """Search for a given image within a region on screen.
    The region is specified by the coordinates and a rectangular region is devised.

    Args:
        path (str): The relative or absolute path to the image to be found.
        x1,y1 (int): The coordinates of the top left of the region to be searched.
        x2,y2 (int): The coordinates of the bottom right of the region to be searched.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        (bool | list[int] | tuple[int, int]): Coordinates if the image is found on screen within the specified region,
            False otherwise.
    """
    try:
        path = resource_path(path)
        pos = imagesearch.imagesearcharea(path, x1, y1, x2, y2, precision)
        return pos if pos[0] != -1 else False
    except Exception:
        return False


def onscreen_region_num_loop(  # pylint: disable=too-many-arguments,disable=invalid-name
    path: str,
    timesample: float,
    max_samples: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    precision: float = 0.8,
) -> bool | list[int] | tuple[int, int]:
    """Search for a given image within a region on screen, attempting multiple times.
    The region is specified by the coordinates and a rectangular region is devised.

    Args:
        path (str): The relative or absolute path to the image to be found.
        timesample (float): The duration between attempts to search the screen.
        max_samples (int): The max number of attempts that the screen will be sampled before giving up.
        x1,y1 (int): The coordinates of the top left of the region to be searched.
        x2,y2 (int): The coordinates of the bottom right of the region to be searched.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        (bool | list[int] | tuple[int, int]): True if the image is found within the specified region, False otherwise.
    """
    try:
        path = resource_path(path)
        return imagesearch_region_num_loop(path, timesample, max_samples, x1, y1, x2, y2, precision)[0] != -1
    except Exception:
        return False


# Via https://github.com/drov0/python-imagesearch/blob/master/python_imagesearch/imagesearch.py
def imagesearch_region_num_loop(  # pylint: disable=too-many-arguments,disable=invalid-name
    image: str,
    timesample: float,
    max_samples: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    precision: float = 0.8,
) -> None | list[int] | tuple[int, int]:
    """Search for a given image within a region on screen, attempting multiple times.
    The region is specified by the coordinates and a rectangular region is devised.

    Args:
        path (str): The relative or absolute path to the image to be found.
        timesample (float): The duration between attempts to search the screen.
        max_samples (int): The max number of attempts that the screen will be sampled before giving up.
        x1,y1 (int): The coordinates of the top left of the region to be searched.
        x2,y2 (int): The coordinates of the bottom right of the region to be searched.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        (bool | list[int] | tuple[int, int]): The coordinates of the image if found within the specified region,
            None otherwise.
    """
    try:
        image = resource_path(image)
        pos = imagesearch.imagesearcharea(image, x1, y1, x2, y2, precision)
        count = 0

        while pos[0] == -1:
            time.sleep(timesample)
            pos = imagesearch.imagesearcharea(image, x1, y1, x2, y2, precision)
            count = count + 1
            if count > max_samples:
                break
        return pos
    except Exception:
        return None


def find_image(path: str, precision: float = 0.8) -> None | list[int] | tuple[int, int]:
    """Search for a given image, returning the coordinates if found.

    Args:
        path (str): The relative or absolute path to the image to be found.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        (None | list[int] | tuple[int, int]): The coordinates of the image if found within the specified region,
            None otherwise.
    """
    try:
        path = resource_path(path)
        pos = imagesearch.imagesearch(path, precision)
        return pos if pos[0] != -1 else None
    except Exception:
        return None


def find_image_multiple_any(paths: list[str], precision: float = 0.8) -> None | list[int] | tuple[int, int]:
    """Search for any of the given images, returning the coordinates of the first one if any are found.

    Args:
        paths (list[str]): The list of relative or absolute paths to images to be searched for.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        (None | list[int] | tuple[int, int]): The coordinates of the image if found within the specified region,
            None otherwise.
    """
    try:
        for path in paths:
            path = resource_path(path)
            pos = imagesearch.imagesearch(path, precision)
            # logger.debug(f"is_onscreen: {pos[0] != -1}") #Advanced debugging not even normally needed
            if pos[0] != -1:
                return pos
            return None
    except Exception as err:
        logger.debug(f"multiple_onscreen_any error: {err}")

    return None


def find_image_in_region_num_loop(  # pylint: disable=too-many-arguments,disable=invalid-name
    path: str,
    timesample: float,
    max_samples: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    precision: float = 0.8,
) -> None | list[int] | tuple[int, int]:
    """Get the coorindates for a given image within a region on screen, attempting multiple times.
    The region is specified by the coordinates and a rectangular region is devised.

    Args:
        path (str): The relative or absolute path to the image to be found.
        timesample (float): The duration between attempts to search the screen.
        max_samples (int): The max number of attempts that the screen will be sampled before giving up.
        x1,y1 (int): The coordinates of the top left of the region to be searched.
        x2,y2 (int): The coordinates of the bottom right of the region to be searched.
        precision (float, optional): The precision to be used when matching the image. Defaults to 0.8.

    Returns:
        (bool | list[int] | tuple[int, int]): The coordinates of the image if found within the specified region,
            None otherwise.
    """
    try:
        path = resource_path(path)
        pos = imagesearch_region_num_loop(path, timesample, max_samples, x1, y1, x2, y2, precision)
        return pos if pos[0] != -1 else None
    except Exception:
        return None
