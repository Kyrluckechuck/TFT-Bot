"""
The main TFT Bot code
"""
import argparse
import configparser
from datetime import datetime
import random
import subprocess
import sys
import time

import keyboard
from loguru import logger
import pyautogui as auto
import pydirectinput

from click_helpers import click_left
from click_helpers import click_right
from click_helpers import click_to_middle
from click_helpers import click_to_middle_multiple
from constants import CONSTANTS
from constants import exit_now_images
from constants import find_match_images
from constants import league_processes
from constants import message_exit_buttons
from constants import wanted_traits
import lcu_integration
from screen_helpers import onscreen
from screen_helpers import onscreen_multiple_any
from screen_helpers import onscreen_region_num_loop
import system_helpers

auto.FAILSAFE = False
GAME_COUNT = 0
PROGRAM_START: datetime
PAUSE_LOGIC = False
PLAY_NEXT_GAME = True
CONFIG = {
    "FF_EARLY": False,
    "VERBOSE": False,
    "OVERRIDE_INSTALL_DIR": None,
}
LCU_INTEGRATION = lcu_integration.LCUIntegration()


def bring_league_client_to_forefront() -> None:
    """Brings the league client to the forefront."""
    try:
        system_helpers.bring_window_to_forefront("League of Legends", CONSTANTS["executables"]["league"]["client_ux"])
    except Exception:
        logger.warning("Failed to bring League client to forefront, this should be non-fatal so let's continue")


def bring_league_game_to_forefront() -> None:
    """Brings the league game to the forefront."""
    try:
        system_helpers.bring_window_to_forefront("League of Legends (TM) Client", CONSTANTS["executables"]["league"]["game"])
    except Exception:
        logger.warning("Failed to bring League game to forefront, this should be non-fatal so let's continue")


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
    return system_helpers.find_in_processes(CONSTANTS["executables"]["league"]["client"]) and system_helpers.find_in_processes(
        CONSTANTS["executables"]["league"]["client_ux"]
    )


def parse_task_kill_text(result: subprocess.CompletedProcess[str]) -> None:
    """Parses the task kill text to log the result.

    Args:
        result (subprocess.CompletedProcess[str]): the return value of the subprocess run.
    """
    if "not found." in result.stderr:
        logger.debug(f"{result.args[-1]} was not running.")
    elif "has been terminated." in result.stdout:
        logger.debug(f"{result.args[-1]} has been terminated.")
    else:
        logger.warning(f"An unknown exception ocurred attempting to end {result.args[-1]}")
        logger.debug(result)


def kill_process(process_executable: str) -> str:
    """Kill the process, and parse whether it was successfully killed

    Args:
        process_executable (str): The process executable to kill

    Returns:
        str: _description_
    """
    return subprocess.run(
        ["taskkill", "/f", "/im", process_executable],
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
        parse_task_kill_text(result)
    time.sleep(1)
    subprocess.run(CONSTANTS["executables"]["league"]["client"], check=True)
    time.sleep(3)
    if not LCU_INTEGRATION.connect_to_lcu(wait_for_availability=True):
        sys.exit(1)


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
    *Note:* This does not entirely stop the bot, but does stop various state changes that can be annoying if you're trying to manually interact with it.
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


def wait_for_league_running() -> bool:
    """Attempt to pause the bot logic evaluation until the league game client is running, or 30 seconds has passed.

    Returns:
        bool: True if the game is running, False otherwise.
    """
    counter = 0
    while not league_game_already_running():
        counter = counter + 1
        time.sleep(0.5)
        if counter > 60:
            logger.info("Timed out, moving on!")
            break
    return league_game_already_running()


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
    """Begin finding a match -- the start of the repeating game logic, dismissing any interruptions and bringing the League client to the forefront/focus."""
    # Queue search loop
    start_queue_repeating = False
    while True:
        if PAUSE_LOGIC:
            time.sleep(5)
            continue

        if not PLAY_NEXT_GAME:
            evaluate_next_game_logic()

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
                time.sleep(1)
                continue

            LCU_INTEGRATION.start_queue()
            time.sleep(1)
            start_queue_repeating = True
            continue

        if not LCU_INTEGRATION.create_lobby():
            time.sleep(5)
    loading_match()


def loading_match() -> None:
    """Attempt to wait for the match to load, bringing the League game to the forefront/focus.
    After some time, if the game has not been detected as starting, it moves on anyways.
    """
    counter = 0
    logger.info("Match loading, waiting for game window (~30s timeout)")
    bring_league_game_to_forefront()
    if not wait_for_league_running():
        if LCU_INTEGRATION.in_game():
            logger.warning(
                "We are in a game, but the game window is not opening. "
                "Restarting client..."
            )
            restart_league_client()
        return

    logger.info("Match loading, waiting for game to start (~120s timeout)")
    while (
        not onscreen(CONSTANTS["game"]["loading"]) and
        not onscreen(CONSTANTS["game"]["gamelogic"]["timer_1"]) and
        not onscreen(CONSTANTS["game"]["round"]["1-"]) and
        not onscreen(CONSTANTS["game"]["round"]["2-"]) and
        not onscreen(CONSTANTS["game"]["round"]["3-"]) and
        not onscreen(CONSTANTS["game"]["round"]["4-"]) and
        not onscreen(CONSTANTS["game"]["round"]["5-"]) and
        not onscreen(CONSTANTS["game"]["round"]["6-"])
    ):
        time.sleep(1)
        bring_league_game_to_forefront()
        if counter > 120:
            logger.warning("Did not detect game start, continuing anyway")
            break
        counter = counter + 1

    logger.info("Match loaded, starting initial draft pathfinding")
    start_match()


def start_match() -> None:
    """Do initial first round pathing to pick the first champ."""
    while onscreen(CONSTANTS["game"]["round"]["1-1"]):
        shared_draft_pathing()
    logger.info("Initial draft complete, continuing with game")
    main_game_loop()


def shared_draft_pathing() -> None:
    """Navigate counter-clockwise in a diamond to help ensure a champ is picked up."""
    auto.moveTo(946, 315)
    click_right()
    time.sleep(2)
    auto.moveTo(700, 450)
    click_right()
    time.sleep(2)
    auto.moveTo(950, 675)
    click_right()
    time.sleep(2)
    auto.moveTo(1200, 460)
    click_right()


def buy(iterations: int) -> None:
    """Attempt to purchase champs with the designated `wanted_traits`.
    This will iterate the attempts, but only if the gold is detected to at least be 1 (to avoid clicking when there is no gold available).

    Args:
        iterations (int): The number of attempts to purchase a champ.
    """
    for i in range(iterations):
        if not check_if_gold_at_least(1):
            return
        for trait in wanted_traits:
            if onscreen(trait):
                click_to_middle(trait)
                time.sleep(0.5)
            else:
                return


def click_ok_message() -> None:
    """Click the message OK button"""
    click_to_middle(CONSTANTS["client"]["messages"]["buttons"]["message_ok"])


def click_exit_message() -> None:
    """Click the message Exit button"""
    click_to_middle_multiple(message_exit_buttons)


def wait_for_internet() -> None:
    """Delay indefinitely until an internet is detected."""
    while not system_helpers.have_internet():
        logger.warning("Internet is not up, will retry in 60 seconds")
        time.sleep(60)


def check_if_client_error() -> bool:
    """Check if any client error is detected.
    If any are detected, the League client is restarted.

    Returns:
        bool: True if a client error message was detected.
    """
    if onscreen(CONSTANTS["client"]["messages"]["down_for_maintenance"]):
        logger.info("League down for maintenance, delaying restart for 5 minutes!")
        return acknowledge_error_and_restart_league(delay=300)
    if onscreen(CONSTANTS["client"]["messages"]["failed_to_reconnect"]):
        logger.info("Failed to reconnect!")
        return acknowledge_error_and_restart_league(internet_pause=True)
    if onscreen(CONSTANTS["client"]["messages"]["login_servers_down"]):
        logger.info("Login servers down!")
        return acknowledge_error_and_restart_league(internet_pause=True)
    if onscreen(CONSTANTS["client"]["messages"]["session_expired"]):
        logger.info("Session expired!")
        return acknowledge_error_and_restart_league()
    if onscreen(CONSTANTS["client"]["messages"]["unexpected_error_with_session"]):
        logger.info("Unexpected error with session!")
        return acknowledge_error_and_restart_league()
    if onscreen(CONSTANTS["client"]["messages"]["unexpected_login_error"]):
        logger.info("Unexpected login error!")
        return acknowledge_error_and_restart_league()
    if onscreen(CONSTANTS["client"]["messages"]["players_are_not_ready"]):
        logger.info("Player not ready detected, waiting to see if it stays")
        time.sleep(5)
        if onscreen(CONSTANTS["client"]["messages"]["players_are_not_ready"]):
            logger.error("Player not ready did not dismiss, restarting client!")
            restart_league_client()
            return True
        logger.info("Player not ready dismissed, continuing on")
    return False


def acknowledge_error_and_restart_league(delay: int = 5, internet_pause: bool = False) -> bool:
    """Acknowledge error message with ok or error button and restart league client
    """
    click_exit_message()
    click_ok_message()
    time.sleep(delay)
    if internet_pause:
        wait_for_internet()
    restart_league_client()
    return True


def exit_now_conditional() -> bool:
    """(Special function for `check_if_game_complete()` conditional.
    Checks if the League game is not running.

    Returns:
        bool: False if the League game is running, True if it is running.
    """
    return not league_game_already_running()


def check_if_game_complete() -> bool:
    """Check if the League game is complete.

    Returns:
        bool: True if any scenario in which the game is not active, False otherwise.
    """
    if onscreen(CONSTANTS["client"]["death"]):
        logger.info("Death detected")
        click_to_middle(CONSTANTS["client"]["death"])
        time.sleep(5)
        return True

    if onscreen_multiple_any(exit_now_images):
        logger.info("End of game detected (exit now)")
        exit_now_bool = click_to_middle_multiple(
            exit_now_images,
            conditional_func=exit_now_conditional,
            delay=1.5
        )
        logger.debug(f"Exit now clicking success: {exit_now_bool}")
        time.sleep(5)
        return True

    if LCU_INTEGRATION.in_game():
        if LCU_INTEGRATION.should_reconnect():
            attempt_reconnect_to_existing_game()
        return False

    return not check_if_client_error()


def attempt_reconnect_to_existing_game() -> bool:
    """If there is a Reconnect button on screen in the client, attempt to reconnect.

    Returns:
        bool: True if a reconnect is attempted, False otherwise.
    """
    if onscreen(CONSTANTS["client"]["reconnect"]):
        logger.info("Reconnecting!")
        click_to_middle(CONSTANTS["client"]["reconnect"])
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


def check_gold(num: int) -> bool:
    try:
        if onscreen_region_num_loop(
                CONSTANTS["game"]["gold"][f"{num}"], 0.05, 5, 780, 850, 970, 920, 0.9
        ):
            logger.debug(f"Found {num} gold")
            return True
    except Exception:
        logger.debug(f"Exception finding {num} gold, we possibly don't have the value as a file")
        # We don't have this gold as a file
        return True
    return False


def check_if_gold_at_least(num: int) -> bool:
    """Check if the gold on screen is at least the provided amount

    Args:
        num (int): The value to check if the gold is at least.

    Returns:
        bool: True if the value is >= `num`, False otherwise.
    """
    logger.debug(f"Looking for at least {num} gold")
    if check_gold(num):
        return True

    for i in range(num + 1):
        if check_gold(i):
            return i >= num

    logger.debug(f"No gold value found, assuming we have more")
    return True


def determine_minimum_round() -> int:
    """
    Determines minimum round we are at.
    Prioritizes PvE markers, falls back to the round display.

    Returns:
        The major round as an integer.

    """
    if (
        onscreen(CONSTANTS["game"]["round"]["krugs_inactive"], 0.9)
        or onscreen(CONSTANTS["game"]["round"]["krugs_active"], 0.9)
    ):
        return 2

    if (
        onscreen(CONSTANTS["game"]["round"]["wolves_inactive"], 0.9)
        or onscreen(CONSTANTS["game"]["round"]["wolves_active"], 0.9)
    ):
        return 3

    if (
        onscreen(CONSTANTS["game"]["round"]["threat_inactive"], 0.9)
        or onscreen(CONSTANTS["game"]["round"]["threat_active"], 0.9)
    ):
        return 4

    if onscreen(CONSTANTS["game"]["round"]["1-"]):
        return 1

    for i in range(1, 7):
        if onscreen(CONSTANTS["game"]["round"][f"{i}-"]):
            return i

    logger.debug("Could not determine minimum round, returning 0.")
    return 0


def main_game_loop() -> None:  # pylint: disable=too-many-branches
    """The main in-game loop.

    Skips 5 second increments if a pause logic request is made, repeating until toggled or an event triggers an early exit.
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
        if minimum_round > 1 and onscreen(CONSTANTS["game"]["round"]["draft_active"], 0.95):
            logger.info("Active draft detected, pathing to carousel")
            shared_draft_pathing()
            continue

        if onscreen(CONSTANTS["game"]["gamelogic"]["choose_an_augment"], 0.95):
            logger.info("Detected augment offer, selecting one")
            auto.moveTo(960, 540)
            click_left()
            time.sleep(0.5)
            continue

        if minimum_round <= 2:
            buy(3)
            continue

        if CONFIG["FF_EARLY"] and minimum_round >= 3:
            logger.info("Attempting to surrender early")
            surrender()
            break

        # If round > 2, buy champs, level and re-roll
        buy(3)
        if check_if_gold_at_least(4) and onscreen(CONSTANTS["game"]["gamelogic"]["xp_buy"]):
            click_to_middle(CONSTANTS["game"]["gamelogic"]["xp_buy"])
            time.sleep(0.2)

        if check_if_gold_at_least(5) and onscreen(CONSTANTS["game"]["gamelogic"]["reroll"]):
            click_to_middle(CONSTANTS["game"]["gamelogic"]["reroll"])
            time.sleep(0.2)
            continue

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

    if not onscreen_multiple_any(find_match_images):
        bring_league_client_to_forefront()
        if check_if_client_error() or not league_client_running():
            return


def match_complete() -> None:
    """Print a log timer to update the time passed and number of games completed (rough estimation), and begin the end of match logic."""
    print_timer()
    logger.info("Match complete! Cleaning up and restarting")
    end_match()


def surrender() -> None:
    """Attempt to surrender.
    """
    random_seconds = random.randint(60, 90)
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
    # FIXME There's a bug in TFT right now where the surrender button
    #  in the settings doesn't work. This is a temporary work-around.
    #  We need to use PyDirectInput since the league client does not
    #  always recognize the input of the method pyautogui uses.
    while not onscreen(CONSTANTS["game"]["surrender"]["surrender_2"]):
        time.sleep(2)
        bring_league_game_to_forefront()
        pydirectinput.write(["enter", "/", "f", "f", "enter"], interval=0.1)
        time.sleep(1)

    click_to_middle(CONSTANTS["game"]["surrender"]["surrender_2"])
    time.sleep(10)
    end_match()
    logger.info("Surrender complete")
    match_complete()


def print_timer() -> None:
    """Print a log timer to update the time passed and number of games completed (rough estimation)."""
    delta = datetime.now() - PROGRAM_START
    duration = datetime.utcfromtimestamp(delta.total_seconds())
    global GAME_COUNT
    GAME_COUNT += 1

    logger.info("-------------------------------------")
    logger.info("Game End")
    logger.info(f"Time since start: {duration.strftime('%H:%M:%S')}")
    logger.info(f"Games played: {str(GAME_COUNT)}")
    logger.info("-------------------------------------")


def tft_bot_loop() -> None:
    """Main loop to ensure various errors don't unhinge/break the bot.
    Since the bot is able to reconnect and handle most errors, this should allow it to resume games in progress even if an 'uncaught exception' has occurred.
    """
    while True:
        try:
            queue()
        except AttributeError:
            logger.info("Not already in game, couldn't find game client on screen, looping")
            time.sleep(5)
            continue


def load_settings():
    """Load settings for the bot.

    Any CLI-set settings take highest precedence, then falling back on config values, then to defaults.
    """
    arg_parser = argparse.ArgumentParser(prog="TFT Bot")
    arg_parser.add_argument(
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

    config = configparser.ConfigParser()
    config.read("bot_settings.ini")

    CONFIG["FF_EARLY"] = parsed_args.ffearly or config.getboolean("SETTINGS", "ForfeitEarly", fallback=False)
    CONFIG["VERBOSE"] = parsed_args.verbose or config.getboolean("SETTINGS", "Verbose", fallback=False)
    CONFIG["OVERRIDE_INSTALL_DIR"] = config.get("SETTINGS", "OverrideInstallLocation", fallback=None)


def update_league_constants(league_install_location: str) -> None:
    """Update League executable constants

    Args:
        league_install_location (str): The determined location for the executables
    """
    logger.debug(
        rf"Updating league install location to {league_install_location}"
    )
    CONSTANTS["executables"]["league"]["client"] = rf"{league_install_location}{CONSTANTS['executables']['league']['client_base']}"
    CONSTANTS["executables"]["league"]["client_ux"] = rf"{league_install_location}{CONSTANTS['executables']['league']['client_ux_base']}"
    CONSTANTS["executables"]["league"]["game"] = rf"{league_install_location}{CONSTANTS['executables']['league']['game_base']}"


def setup_hotkeys() -> None:
    """Setup hotkey listeners"""
    keyboard.add_hotkey("alt+p", lambda: toggle_pause())  # pylint: disable=unnecessary-lambda
    keyboard.add_hotkey("alt+n", lambda: toggle_play_next_game())  # pylint: disable=unnecessary-lambda


@logger.catch
def main():
    """Entrypoint function to initialize most of the code.

    Parses command line arguments, sets up console settings, logging, and kicks of the main bot loop.
    """
    load_settings()

    # Normal logging
    if CONFIG["VERBOSE"]:
        logger.level("DEBUG")
    else:
        # We need to remove the default logger if we want to
        # change the default format.
        # The supplied format is the default one, minus the module.
        logger.remove()
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> - "
                "<level>{message}</level>"
            ),
            level="INFO"
        )

    # File logging, writes to a file in the same folder as the executable.
    # Logs at level DEBUG, so it's always verbose.
    # retention=10 to only keep the 10 most recent files.
    logger.add("tft-bot-debug-{time}.log", level="DEBUG", retention=10)

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
    logger.info(
        f"Bot will {'' if CONFIG['VERBOSE'] else 'NOT '}be verbose "
        f"(display debug messages)."
    )
    logger.info(
        f"Bot will {'' if CONFIG['FF_EARLY'] else 'NOT '}surrender early."
    )

    logger.info("Welcome! Please feel free to ask questions or contribute at https://github.com/Kyrluckechuck/tft-bot")
    if (
        auto.confirm(
            title="TFT Auto Bot",
            text="Press Start when the bot should continue!\n",
            buttons=["Start", "Cancel"],
        )
        != "Start"
    ):
        logger.warning("Initialization completed but aborting by user choice")
        sys.exit(1)

    setup_hotkeys()

    if not lcu_integration.get_lcu_process():
        logger.warning("League client is not open, attempting to start it")
        league_directory = system_helpers.determine_league_install_location(
            CONFIG["OVERRIDE_INSTALL_DIR"]
        )
        update_league_constants(league_directory)
        restart_league_client()
    elif not LCU_INTEGRATION.connect_to_lcu():
        sys.exit(1)

    league_directory = LCU_INTEGRATION.get_installation_directory()
    update_league_constants(league_directory)

    global PROGRAM_START
    PROGRAM_START = datetime.now()
    tft_bot_loop()


if __name__ == "__main__":
    sys.exit(main())
