"""
Module to handle the configuration for the bot.
"""
import argparse
import os.path
import shutil
from typing import Any

from loguru import logger
from ruamel.yaml import YAML

from .helpers import system_helpers

_SELF: dict[str, Any] = {}


def load_config(storage_path: str) -> None:
    """
    Writes the configuration from resource (provided in repository) to storage path, loads the configuration from
    storage path to memory and updates the configuration if necessary.

    Args:
        storage_path: The base storage path where all of our files should go.

    """
    yaml = YAML()

    config_resource_path = system_helpers.resource_path("tft_bot/resources/config.yaml")
    config_path = f"{storage_path}\\config.yaml"

    if not os.path.isfile(config_path):
        shutil.copyfile(config_resource_path, config_path)

    with open(config_resource_path, mode="r", encoding="UTF-8") as config_resource:
        _config_resource: dict[str, Any] = yaml.load(config_resource)

    with open(config_path, mode="r", encoding="UTF-8") as config_file:
        global _SELF
        _SELF = yaml.load(config_file)

    if _config_resource.get("version") > _SELF.get("version", 0):
        logger.warning("Config is outdated, creating a back-up and updating it")

        shutil.copyfile(config_path, f"{config_path}.bak")

        _config_resource.update((key, _SELF[key]) for key in _SELF.keys() & _config_resource.keys() if key != "version")
        with open(config_path, mode="w", encoding="UTF-8") as config_file:
            yaml.dump(_config_resource, config_file)

        _SELF = _config_resource

    _parse_cli_flags()


def _parse_cli_flags() -> None:
    """
    Override settings for the bot with CLI flags, since they take higher precedence.
    """
    arg_parser = argparse.ArgumentParser(prog="TFT Bot")
    arg_parser.add_argument(
        "-f",
        "--ffearly",
        action="store_true",
        help="If the game should be surrendered at first available time.",
    )
    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity, mostly useful for debugging",
    )
    parsed_args = arg_parser.parse_args()

    if parsed_args.ffearly:
        _SELF["forfeit_early"] = True

    if parsed_args.verbose:
        _SELF["verbose"] = True


def verbose() -> bool:
    """
    Get the state of the verbose setting in the config.

    Returns:
        True if we should be verbose, False if not.

    """
    return _SELF.get("verbose", False)


def forfeit_early() -> bool:
    """
    Get the state of the forfeit_early setting in the config.

    Returns:
        True if we should surrender early, False if not.

    """
    return _SELF.get("forfeit_early", False)


def get_override_install_location() -> str | None:
    """
    Get the value of the override_install_location setting in the config.

    Returns:
        An optional string containing the user-defined install location.

    """
    return _SELF.get("override_install_location") or None


def get_wanted_traits() -> list[str]:
    """
    Get the list of traits we attempt to purchase.

    Returns:
        A list of traits we look for.

    """
    return _SELF.get("wanted_traits", ["duelist", "brawler"])


def purchase_traits_in_prioritized_order() -> bool:
    """
    Get if we should purchase traits in prioritized order.

    Returns:
        True if we should only buy a trait if the trait before it has been found, False if not.

    """
    return _SELF.get("purchase_traits_in_prioritized_order", True)
