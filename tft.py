"""
The main TFT Bot code
"""
from datetime import datetime
import os
import random
import subprocess
import sys
import time
import webbrowser

import keyboard
from loguru import logger
import psutil
import pyautogui as auto
import pydirectinput
import requests
from requests import HTTPError

from tft_bot import config
from tft_bot.constants import CONSTANTS
from tft_bot.constants import exit_now_images
from tft_bot.constants import league_processes
from tft_bot.constants import message_exit_buttons
from tft_bot.economy.base import EconomyMode
from tft_bot.helpers import system_helpers
from tft_bot.helpers.click_helpers import click_to
from tft_bot.helpers.click_helpers import click_to_image
from tft_bot.helpers.screen_helpers import calculate_window_click_offset
from tft_bot.helpers.screen_helpers import check_league_game_size
from tft_bot.helpers.screen_helpers import get_board_positions
from tft_bot.helpers.screen_helpers import get_on_screen_in_client
from tft_bot.helpers.screen_helpers import get_on_screen_in_game
from tft_bot.league_api import league_api_integration

auto.FAILSAFE = False
GAME_COUNT = 0
PROGRAM_START: datetime
LAST_TIMER_PRINTED_AT: datetime = datetime.now()
PAUSE_LOGIC = False
PLAY_NEXT_GAME = True
LCU_INTEGRATION = league_api_integration.LCUIntegration()
GAME_CLIENT_INTEGRATION = league_api_integration.GameClientIntegration()


@logger.catch
def bring_league_client_to_forefront() -> None:
    """Brings the league client to the forefront."""
    system_helpers.bring_window_to_forefront(
        CONSTANTS["window_titles"]["client"], CONSTANTS["executables"]["league"]["client_ux"]
    )


@logger.catch
def bring_league_game_to_forefront() -> None:
    """Brings the league game to the forefront."""
    system_helpers.bring_window_to_forefront(
        CONSTANTS["window_titles"]["game"], CONSTANTS["executables"]["league"]["game"]
    )


def league_game_already_running() -> bool:
    """Checks if the league game is already running.

    Returns:
        bool: True if the game is running, False otherwise.
    """
    return system_helpers.find_in_processes(CONSTANTS["executables"]["league"]["game"])


def league_client_running() -> bool:
    """Checks if the league client is already running.

    Returns:
        bool: True if the client is running, False otherwise.
    """
    return system_helpers.find_in_processes(
        CONSTANTS["executables"]["league"]["client"]
    ) and system_helpers.find_in_processes(CONSTANTS["executables"]["league"]["client_ux"])


def parse_task_kill_result(result: subprocess.CompletedProcess[str]) -> None:
    """Parses the task kill text to log the result.

    Args:
        result (subprocess.CompletedProcess[str]): the return value of the subprocess run.
    """
    if result.returncode == 128:
        logger.debug(f"{result.args[-1]} was not running.")
    elif result.returncode == 0:
        logger.debug(f"{result.args[-1]} has been terminated.")
    else:
        logger.warning(f"An  error was received while trying to ending {result.args[-1]}")
        logger.debug(result.stderr)


def kill_process(process_executable: str, force: bool = True) -> subprocess.CompletedProcess[str]:
    """Kill the process, and parse whether it was successfully killed

    Args:
        process_executable (str): The process executable to kill
        force (bool): Whether to force the process termination

    Returns:
        str: _description_
    """
    task_kill_args = ["taskkill", "/im", process_executable]
    if force:
        task_kill_args.insert(1, "/f")
    return subprocess.run(
        task_kill_args,
        check=False,
        capture_output=True,
        text=True,
    )


def restart_league_client() -> None:
    """Restarts the league client."""
    logger.debug("Killing League Processes!")
    for process_to_kill in league_processes:
        logger.debug(f"Killing {process_to_kill}")
        result = kill_process(process_to_kill)
        parse_task_kill_result(result)
    time.sleep(1)

    if not system_helpers.internet():
        wait_for_internet()
        time.sleep(1)

    subprocess.run(CONSTANTS["executables"]["league"]["client"], check=True)
    time.sleep(3)
    if not LCU_INTEGRATION.connect_to_lcu(wait_for_availability=True):
        restart_league_client()


def restart_league_if_not_running() -> bool:
    """Restarts the league client if it is not already running.

    Returns:
        bool: True if the league client was restarted, False otherwise.
    """
    if not league_client_running():
        logger.debug("League client not detected, restarting!")
        restart_league_client()
        return True
    return False


def toggle_pause() -> None:
    """Toggles whether the bots logic evaluation should pause.
    *Note:* This does not entirely stop the bot, but does stop various state changes that can be annoying if you're
    trying to manually interact with it.
    """
    global PAUSE_LOGIC
    logger.debug(f"alt+p pressed, toggling pause from {PAUSE_LOGIC} to {not PAUSE_LOGIC}")
    PAUSE_LOGIC = not PAUSE_LOGIC
    if PAUSE_LOGIC:
        logger.warning("Bot now paused, remember to unpause to continue botting!")
    else:
        logger.warning("Bot playing again!")


def toggle_play_next_game() -> None:
    """Toggles whether the bots logic evaluation should start a new game after this finishes.
    *Note:* This does not entirely stop the bot, but will stop it from starting a new game.
    """
    global PLAY_NEXT_GAME
    logger.debug(f"alt+n pressed, toggling pause from {PLAY_NEXT_GAME} to {not PLAY_NEXT_GAME}")
    PLAY_NEXT_GAME = not PLAY_NEXT_GAME
    if not PLAY_NEXT_GAME:
        logger.warning("Bot will not queue a new game when a lobby is detected!")
    else:
        logger.warning("Bot will queue a new game when in lobby!")


def evaluate_next_game_logic() -> None:
    """Don't queue next game, but continue current if already playing.

    Wait indefinitely if not already in-game.
    """
    if not league_game_already_running():
        logger.warning("Play next game disabled, waiting for user to toggle or program close")
        wait_counter = 0
        while not PLAY_NEXT_GAME:
            sleep_time = 30
            if wait_counter > 0:
                logger.debug(f"Play next game still disabled after {sleep_time * wait_counter} seconds")
            time.sleep(sleep_time)
            wait_counter = wait_counter + 1
    else:
        logger.warning("Play next game disabled, but game already in progress, will not resume next cycle")


# Start between match logic


@logger.catch
def queue() -> None:  # pylint: disable=too-many-branches
    """Begin finding a match -- the start of the repeating game logic."""
    # Queue search loop
    start_queue_repeating = False
    while True:
        if PAUSE_LOGIC:
            time.sleep(5)
            continue

        if not PLAY_NEXT_GAME:
            evaluate_next_game_logic()

        if LCU_INTEGRATION.session_expired():
            logger.warning("Our login session expired, restarting the client")
            restart_league_client()
            time.sleep(5)
            continue

        if LCU_INTEGRATION.in_game():
            logger.info("A game is running, switching to game logic")
            break

        if LCU_INTEGRATION.in_queue():
            start_queue_repeating = False
            if LCU_INTEGRATION.found_queue() and not LCU_INTEGRATION.queue_accepted():
                LCU_INTEGRATION.accept_queue()
                time.sleep(3)
            else:
                time.sleep(3)
            continue

        if not PLAY_NEXT_GAME:
            continue

        if LCU_INTEGRATION.in_lobby():
            # Fix for if the user is considered not ready.
            if start_queue_repeating:
                LCU_INTEGRATION.delete_lobby()
                start_queue_repeating = False
                time.sleep(3)
                continue

            LCU_INTEGRATION.start_queue()
            time.sleep(3)
            start_queue_repeating = True
            continue

        if not LCU_INTEGRATION.create_lobby():
            time.sleep(5)
    loading_match()


def loading_match() -> None:
    """Attempt to wait for the match to load, bringing the League game to the forefront/focus.
    After some time, if the game has not been detected as starting, it moves on anyway.
    """
    game_window_timeout = config.get_timeout(config.Timeout.GAME_WINDOW, 30)
    logger.info(f"Waiting for the game window (~{game_window_timeout}s timeout)")
    if not GAME_CLIENT_INTEGRATION.wait_for_game_window(lcu_integration=LCU_INTEGRATION, timeout=game_window_timeout):
        if LCU_INTEGRATION.in_game():
            logger.warning("We are in a game, but the game window is not opening. Restarting client...")
            restart_league_client()
        return

    game_start_timeout = config.get_timeout(config.Timeout.GAME_START, 120)
    logger.info(f"Match loading, waiting for game to start (~{game_start_timeout}s timeout)")
    for _ in range(game_start_timeout):
        if GAME_CLIENT_INTEGRATION.game_loaded():
            break
        time.sleep(1)
    else:
        logger.warning("Did not detect game start, continuing anyway. This means things COULD break, but shouldn't")

    logger.info("Match loaded, starting initial draft pathfinding")
    bring_league_game_to_forefront()
    check_league_game_size()
    start_match()


def start_match() -> None:
    """Do initial first round pathing to pick the first champ."""
    while get_on_screen_in_game(CONSTANTS["game"]["round"]["1-1"]):
        shared_draft_pathing()
    logger.info("Initial draft complete, continuing with game")
    main_game_loop(economy_mode=config.get_economy_mode(system_helpers=system_helpers))


def shared_draft_pathing() -> None:
    """Navigate counter-clockwise in a diamond to help ensure a champ is picked up."""
    top = calculate_window_click_offset(window_title=CONSTANTS["window_titles"]["game"], position_x=946, position_y=315)
    left = calculate_window_click_offset(
        window_title=CONSTANTS["window_titles"]["game"], position_x=700, position_y=450
    )
    bottom = calculate_window_click_offset(
        window_title=CONSTANTS["window_titles"]["game"], position_x=950, position_y=675
    )
    right = calculate_window_click_offset(
        window_title=CONSTANTS["window_titles"]["game"], position_x=1200, position_y=460
    )
    click_to(position_x=top.position_x, position_y=top.position_y, action="right")
    time.sleep(2)
    click_to(position_x=left.position_x, position_y=left.position_y, action="right")
    time.sleep(2)
    click_to(position_x=bottom.position_x, position_y=bottom.position_y, action="right")
    time.sleep(2)
    click_to(position_x=right.position_x, position_y=right.position_y, action="right")


def click_ok_message() -> None:
    """Click the message OK button"""
    click_to_image(
        image_search_result=get_on_screen_in_client(CONSTANTS["client"]["messages"]["buttons"]["message_ok"])
    )


def click_exit_message() -> None:
    """Click the message Exit button"""
    for button in message_exit_buttons:
        click_to_image(image_search_result=get_on_screen_in_client(button))


def wait_for_internet() -> None:
    """Delay indefinitely until an internet is detected."""
    while not system_helpers.internet():
        logger.warning("Internet is not up, will retry in 60 seconds")
        time.sleep(60)


def check_if_client_error() -> bool:  # pylint: disable=too-many-return-statements
    """Check if any client error is detected.
    If any are detected, the League client is restarted.

    Returns:
        bool: True if a client error message was detected.
    """
    if get_on_screen_in_client(CONSTANTS["client"]["messages"]["down_for_maintenance"]):
        logger.info("League down for maintenance, delaying restart for 5 minutes!")
        return acknowledge_error_and_restart_league(delay=300)
    if get_on_screen_in_client(CONSTANTS["client"]["messages"]["failed_to_reconnect"]):
        logger.info("Failed to reconnect!")
        return acknowledge_error_and_restart_league()
    if get_on_screen_in_client(CONSTANTS["client"]["messages"]["login_servers_down"]):
        logger.info("Login servers down!")
        return acknowledge_error_and_restart_league()
    if get_on_screen_in_client(CONSTANTS["client"]["messages"]["session_expired"]):
        logger.info("Session expired!")
        return acknowledge_error_and_restart_league()
    if get_on_screen_in_client(CONSTANTS["client"]["messages"]["unexpected_error_with_session"]):
        logger.info("Unexpected error with session!")
        return acknowledge_error_and_restart_league()
    if get_on_screen_in_client(CONSTANTS["client"]["messages"]["unexpected_login_error"]):
        logger.info("Unexpected login error!")
        return acknowledge_error_and_restart_league()
    return False


def acknowledge_error_and_restart_league(delay: int = 5) -> bool:
    """Acknowledge error message with ok or error button and restart league client"""
    click_exit_message()
    click_ok_message()
    time.sleep(delay)
    restart_league_client()
    return True


def exit_now_conditional() -> bool:
    """(Special function for `check_if_game_complete()` conditional.
    Checks if the League game is not running.

    Returns:
        bool: False if the League game is running, True if it is running.
    """
    return not league_game_already_running()


def check_screen_for_exit_button() -> bool:
    """
    Checks the screen for any exit buttons we expect to appear when the player dies.

    Returns:
        True if any known exit buttons were found, False if not.

    """
    for image in exit_now_images:
        if click_to_image(image_search_result=get_on_screen_in_game(image)):
            logger.info("End of game detected, exiting")
            break
    else:
        return False

    time.sleep(5)
    return True


def check_if_game_complete(wait_for_exit_buttons: bool = False) -> bool:
    """Check if the League game is complete.

    Returns:
        bool: True if any scenario in which the game is not active, False otherwise.
    """
    if wait_for_exit_buttons:
        exit_button_timeout = config.get_timeout(config.Timeout.EXIT_BUTTON, 25)
        logger.info(f"Waiting an additional ~{exit_button_timeout}s for any exit buttons")
        for _ in range(exit_button_timeout - 1):
            if check_screen_for_exit_button():
                return True
            time.sleep(1)

    if check_screen_for_exit_button():
        return True

    if LCU_INTEGRATION.in_game():
        if LCU_INTEGRATION.should_reconnect():
            attempt_reconnect_to_existing_game()

        if GAME_CLIENT_INTEGRATION.is_dead():
            if not wait_for_exit_buttons:
                logger.info("The game considers us dead, checking the screen again for exit buttons")
                return check_if_game_complete(wait_for_exit_buttons=True)

            logger.warning("We are in-game and considered dead, but no death button has been found. Exiting gracefully")
            # A non-forceful taskkill tries to tell the process to exit gracefully, similar to Alt+F4.
            # The first request opens the "Are you sure you want to exit?" window.
            parse_task_kill_result(kill_process(CONSTANTS["processes"]["game"], force=False))
            # The second request "confirms" the wish.
            parse_task_kill_result(kill_process(CONSTANTS["processes"]["game"], force=False))
            graceful_exit_timeout = config.get_timeout(config.Timeout.GRACEFUL_EXIT, 60)
            logger.info(f"Waiting ~{graceful_exit_timeout}s for graceful exit")
            for _ in range(graceful_exit_timeout):
                if not LCU_INTEGRATION.in_game():
                    break
                time.sleep(1)
            else:
                logger.error("Game did not exit gracefully, restarting everything to be safe")
                restart_league_client()
            return True

        if LCU_INTEGRATION.session_expired():
            logger.warning("Our session expired while we were in a game. We have to restart")
            restart_league_client()

        return False

    return not check_if_client_error()


def attempt_reconnect_to_existing_game() -> bool:
    """If there is a Reconnect button on screen in the client, attempt to reconnect.

    Returns:
        bool: True if a reconnect is attempted, False otherwise.
    """
    if LCU_INTEGRATION.should_reconnect():
        LCU_INTEGRATION.reconnect()
        logger.info("Reconnecting!")
        return True
    return False


def check_if_post_game() -> bool:
    """Checks to see if the game was interrupted.

    Returns:
        bool: True if the game was complete or a reconnection attempt is made, False otherwise.
    """
    game_complete = check_if_game_complete()
    if game_complete:
        return True
    return attempt_reconnect_to_existing_game()


def determine_minimum_round() -> int:
    """
    Determines minimum round we are at.
    Prioritizes PvE markers, falls back to the round display.

    Returns:
        The major round as an integer.

    """
    if get_on_screen_in_game(CONSTANTS["game"]["round"]["krugs_inactive"], 0.9) or get_on_screen_in_game(
        CONSTANTS["game"]["round"]["krugs_active"], 0.9
    ):
        return 2

    if get_on_screen_in_game(CONSTANTS["game"]["round"]["wolves_inactive"], 0.9) or get_on_screen_in_game(
        CONSTANTS["game"]["round"]["wolves_active"], 0.9
    ):
        return 3

    if get_on_screen_in_game(CONSTANTS["game"]["round"]["threat_inactive"], 0.9) or get_on_screen_in_game(
        CONSTANTS["game"]["round"]["threat_active"], 0.9
    ):
        return 4

    if get_on_screen_in_game(CONSTANTS["game"]["round"]["1-"]):
        return 1

    for i in range(1, 7):
        if get_on_screen_in_game(CONSTANTS["game"]["round"][f"{i}-"]):
            return i

    logger.debug("Could not determine minimum round, returning 0.")
    return 0


def main_game_loop(economy_mode: EconomyMode) -> None:
    """
    The main in-game loop.

    Args:
        economy_mode: The economy mode the bot should use

    Skips 5-second increments if a pause logic request is made,
    repeating until toggled or an event triggers an early exit.
    """
    while True:
        if PAUSE_LOGIC:
            time.sleep(5)
            continue

        post_game = check_if_post_game()
        if post_game:
            match_complete()
            break

        minimum_round = determine_minimum_round()
        # Free champ round
        if minimum_round > 1 and get_on_screen_in_game(CONSTANTS["game"]["round"]["draft_active"], 0.95):
            logger.info("Active draft detected, pathing to carousel")
            shared_draft_pathing()
            continue

        if get_on_screen_in_game(CONSTANTS["game"]["gamelogic"]["choose_an_augment"], 0.95):
            logger.info("Detected augment offer, selecting one")
            augment_offset = calculate_window_click_offset(
                window_title=CONSTANTS["window_titles"]["game"], position_x=960, position_y=540
            )
            click_to(position_x=augment_offset.position_x, position_y=augment_offset.position_y)
            time.sleep(3)

            logger.debug(f"Board positions: {get_board_positions()}")
            continue

        economy_mode.loop_decision(minimum_round=minimum_round)

        if minimum_round >= 3 and config.forfeit_early():
            logger.info("Attempting to surrender early")
            surrender()
            break

        time.sleep(0.5)


def end_match() -> None:
    """End of TFT game logic.

    Loops to ensure we are no longer in a game.

    Will check for client errors that require a restart.
    """
    counter = 0
    while True:
        if counter >= 60:
            restart_league_client()
            return
        if LCU_INTEGRATION.in_game():
            counter += 1
            time.sleep(1)
            continue
        break

    bring_league_client_to_forefront()
    time.sleep(10)
    check_if_client_error()


def match_complete() -> None:
    """Print a log timer to update the time passed and number of games completed (rough estimation),
    and begin the end of match logic.
    """
    print_timer()
    logger.info("Match complete! Cleaning up and restarting")
    end_match()


def surrender() -> None:
    """Attempt to surrender."""
    random_seconds = random.randint(
        config.get_timeout(config.Timeout.SURRENDER_MIN, 60), config.get_timeout(config.Timeout.SURRENDER_MAX, 90)
    )
    logger.info(f"Waiting {random_seconds} seconds before surrendering...")
    time.sleep(random_seconds)
    logger.info("Starting surrender")
    # click_to_middle(CONSTANTS["game"]["settings"])
    #
    # counter = 0
    # while not onscreen(CONSTANTS["game"]["surrender"]["surrender_1"]):
    #     # just in case it gets interrupted or misses
    #     click_to_middle(CONSTANTS["game"]["settings"])
    #     time.sleep(1)
    #     counter = counter + 1
    #     if counter > 20:
    #         break
    # while not onscreen(CONSTANTS["game"]["surrender"]["surrender_2"]):
    #     click_to_middle(CONSTANTS["game"]["surrender"]["surrender_1"])
    #     # added a check here for the rare case that the game ended before the surrender finished.
    #     if check_if_post_game():
    #         return
    #     counter = counter + 1
    #     if counter > 20:
    #         break
    # FIXME There's a bug in TFT right now where the surrender button  # pylint: disable=fixme
    #  in the settings doesn't work. This is a temporary work-around.
    #  We need to use PyDirectInput since the league client does not
    #  always recognize the input of the method pyautogui uses.
    while not click_to_image(image_search_result=get_on_screen_in_game(CONSTANTS["game"]["surrender"]["surrender_2"])):
        time.sleep(2)
        bring_league_game_to_forefront()
        pydirectinput.write(["enter", "/", "f", "f", "enter"], interval=0.1)
        time.sleep(1)

    time.sleep(10)
    end_match()
    logger.info("Surrender complete")
    match_complete()


def print_timer() -> None:
    """Print a log timer to update the time passed and number of games completed (rough estimation)."""
    global LAST_TIMER_PRINTED_AT
    now = datetime.now()
    if (now - LAST_TIMER_PRINTED_AT).total_seconds() < 300:
        return

    delta_seconds = int((now - PROGRAM_START).total_seconds())
    global GAME_COUNT
    GAME_COUNT += 1

    logger.info("-----------------------------------------")
    logger.info("Game End")
    logger.info(f"Time since start: {delta_seconds // 3600}h {(delta_seconds // 60) % 60}m {delta_seconds % 60}s")
    logger.info(f"Games played: {str(GAME_COUNT)}")
    logger.info(f"Win rate (at most last 20 games): {LCU_INTEGRATION.get_win_rate(GAME_COUNT)}%")
    logger.info("-----------------------------------------")

    LAST_TIMER_PRINTED_AT = datetime.now()


def tft_bot_loop() -> None:
    """Main loop to ensure various errors don't unhinge/break the bot.
    Since the bot is able to reconnect and handle most errors,
    this should allow it to resume games in progress even if an 'uncaught exception' has occurred.
    """
    while True:
        try:
            queue()
        except AttributeError:
            logger.info("Not already in game, couldn't find game client on screen, looping")
            time.sleep(5)
            continue


def update_league_constants(league_install_location: str) -> None:
    """Update League executable constants

    Args:
        league_install_location (str): The determined location for the executables
    """
    logger.debug(rf"Updating league install location to {league_install_location}")
    CONSTANTS["executables"]["league"][
        "client"
    ] = rf"{league_install_location}{CONSTANTS['executables']['league']['client_base']}"
    CONSTANTS["executables"]["league"][
        "client_ux"
    ] = rf"{league_install_location}{CONSTANTS['executables']['league']['client_ux_base']}"
    CONSTANTS["executables"]["league"][
        "game"
    ] = rf"{league_install_location}{CONSTANTS['executables']['league']['game_base']}"


def setup_hotkeys() -> None:
    """Setup hotkey listeners"""
    keyboard.add_hotkey("alt+p", lambda: toggle_pause())  # pylint: disable=unnecessary-lambda
    keyboard.add_hotkey("alt+n", lambda: toggle_play_next_game())  # pylint: disable=unnecessary-lambda


def get_newer_version() -> tuple[str, str] | None:
    """
    Get any newer version from GitHub.

    Returns:
        A tuple of local version and repository version, or None if there is no newer version.

    """
    update_notifier_timeout = config.get_timeout(config.Timeout.UPDATE_NOTIFIER, 10)
    logger.info(f"Checking if there is a newer version ({update_notifier_timeout}s timeout)")
    try:
        repository_version_response = requests.get(
            "https://api.github.com/repos/Kyrluckechuck/TFT-Bot/releases/latest", timeout=update_notifier_timeout
        )
    except requests.exceptions.Timeout:
        logger.debug("Could not connect to GitHub API, continuing as if there is no newer version")
        return None

    try:
        repository_version_response.raise_for_status()
    except HTTPError as err:
        logger.opt(exception=err).debug("There was an error fetching the latest version")
        return None

    repository_version = repository_version_response.json()["tag_name"].replace("v", "").split(".")

    with open("VERSION", mode="r", encoding="UTF-8") as version_file:
        local_version = version_file.readline().replace("\r", "").replace("\n", "").split(".")

    for i in range(3):
        if repository_version[i] > local_version[i]:
            return ".".join(local_version), ".".join(repository_version)

    return None


def re_add_non_debug_logger(log_level: str) -> None:
    """
    Remove all loggers and add our formatted logger at a desired level.
    Since loguru is not loggers in a strict sense but more about log handlers that do not care about the level,
    there is no straight setLevel method. So to change the level, we have to re-add it.

    Args:
        log_level: The level to log at.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> - "
            "<level>{message}</level>"
        ),
        level=log_level,
    )


def check_for_new_version(repository_url: str):
    """
    Checks the given repository for a newer version than the one stored.

    Args:
        repository_url: The repository URL to check the version at.
    """
    releases_url = f"{repository_url}/releases/latest"
    versions = get_newer_version()
    if versions:
        logger.warning("There is a newer version available")
        if (
            auto.confirm(
                title="TFT Auto Bot",
                text=(
                    "There is a newer version available!\n"
                    f"Your version: {versions[0]}\n"
                    f"Current version: {versions[1]}"
                ),
                buttons=["Download", "Ignore"],
            )
            == "Download"
        ):
            logger.info(f"{releases_url} should open in your browser now")
            webbrowser.open(f"{releases_url}", new=0, autoraise=True)
            sys.exit(0)
    else:
        logger.info("You're up to date!")


def wait_for_start_confirmation():
    """
    Prompts the user to confirm that they want to start the bot.
    """
    if (
        auto.confirm(
            title="TFT Auto Bot",
            text="Press Start when the bot should continue!\n",
            buttons=["Start", "Cancel"],
        )
        != "Start"
    ):
        logger.warning("Initialization completed but aborting by user choice")
        sys.exit(0)


@logger.catch
def main():
    """Entrypoint function to initialize most of the code.

    Parses command line arguments, sets up console settings, logging, and kicks of the main bot loop.
    """
    # This enables us to always use relative paths and avoid unicode issues in paths.
    os.chdir(getattr(sys, "_MEIPASS", os.path.abspath(".")))

    storage_path = "output"
    for process in psutil.process_iter():
        if process.name() in {"TFT Bot.exe", "TFT.Bot.exe"}:
            storage_path = system_helpers.expand_environment_variables(CONSTANTS["storage"]["appdata"])
            break

    config.load_config(storage_path=storage_path)

    log_level = config.get_log_level().upper()
    if log_level == "DEBUG":
        logger.level("DEBUG")
    else:
        re_add_non_debug_logger("INFO")

    # File logging, writes to a file in the same folder as the executable.
    # Logs at level DEBUG, so it's always verbose.
    # retention=10 to only keep the 10 most recent files.
    logger.add(storage_path + "\\tft-bot-debug-{time}.log", level="DEBUG", retention=10)
    system_helpers.disable_quickedit()
    # Start auth + main script
    logger.info(
        r"""Initial codebase by:
         _____       _                            _
        |  __ \     | |                          | |
        | |  | | ___| |_ ___ _ __ __ _  ___ _ __ | |_
        | |  | |/ _ \ __/ _ \ '__/ _` |/ _ \ '_ \| __|
        | |__| |  __/ ||  __/ | | (_| |  __/ | | | |_
        |_____/ \___|\__\___|_|  \__, |\___|_| |_|\__|
                                  __/ |
                                 |___/
        """
    )
    logger.info(
        r"""Re-written by:
        __ __              __              __                __                  __
       / //_/__  __ _____ / /__  __ _____ / /__ ___   _____ / /_   __  __ _____ / /__
      / ,<  / / / // ___// // / / // ___// //_// _ \ / ___// __ \ / / / // ___// //_/
     / /| |/ /_/ // /   / // /_/ // /__ / ,<  /  __// /__ / / / // /_/ // /__ / ,<
    /_/ |_|\__, //_/   /_/ \__,_/ \___//_/|_| \___/ \___//_/ /_/ \__,_/ \___//_/|_|
          /____/
        """
    )

    logger.info("===== TFT Bot Started =====")
    logger.info(f"Bot will only display messages at severity level {log_level}.")
    logger.info(f"Bot will {'' if config.forfeit_early() else 'NOT '}surrender early.")

    absolute_storage_path = os.path.abspath(storage_path)
    if not os.access(absolute_storage_path, os.W_OK):
        logger.error(f"We do not have write access into {absolute_storage_path}. Try running the bot as administrator.")
    else:
        logger.info(f"All of the logs and configuration can be found in '{absolute_storage_path}'.")

    repository_url = "https://github.com/Kyrluckechuck/tft-bot"
    logger.info(f"Welcome! Please feel free to ask questions or contribute at {repository_url}")

    check_for_new_version(repository_url=repository_url)
    wait_for_start_confirmation()

    # After having displayed all of our start-up information, we respect the user's choice of log level
    # and re-create the logging handler, if necessary.
    if log_level not in {"DEBUG", "INFO"}:
        re_add_non_debug_logger(log_level)

    setup_hotkeys()

    if not league_api_integration.get_lcu_process():
        logger.warning("League client is not open, attempting to start it")
        league_directory = system_helpers.determine_league_install_location()
        update_league_constants(league_directory)
        restart_league_client()
    elif not LCU_INTEGRATION.connect_to_lcu():
        restart_league_client()

    league_directory = LCU_INTEGRATION.get_installation_directory()
    update_league_constants(league_directory)

    global PROGRAM_START
    PROGRAM_START = datetime.now()
    tft_bot_loop()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Received wish to exit by CTRL+C, exiting")
        print_timer()
        sys.exit(0)
