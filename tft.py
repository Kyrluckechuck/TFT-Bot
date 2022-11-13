"""
The main TFT Bot code
"""
import argparse
import logging
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import keyboard
import pyautogui as auto
from printy import printy

import system_helpers
from click_helpers import click_right, click_to_middle, click_to_middle_multiple
from constants import CONSTANTS, exit_now_images, find_match_images, key_fragment_images, skip_waiting_for_stats_images, wanted_traits
from logging_helper import setup_logging
from screen_helpers import onscreen, onscreen_multiple_any, onscreen_region_numLoop

auto.FAILSAFE = False
GAME_COUNT = -1
END_TIMER = time.time()
START_TIMER = time.time()
PAUSE_LOGIC = False
FF_EARLY = False
VERBOSE = False

def bring_league_client_to_forefront() -> None:
    """Brings the league client to the forefront."""
    try:
        system_helpers.bring_window_to_forefront("League of Legends", CONSTANTS['executables']['league']['client_ux'])
    except Exception:
        logging.warning("Failed to bring League client to forefront, this should be non-fatal so let's continue")

def bring_league_game_to_forefront() -> None:
    """Brings the league game to the forefront."""
    try:
        system_helpers.bring_window_to_forefront("League of Legends", CONSTANTS['executables']['league']['game'])
    except Exception:
        logging.warning("Failed to bring League game to forefront, this should be non-fatal so let's continue")

def league_game_already_running() -> bool:
    """Checks if the league game is already running.

    Returns:
        bool: True if the game is running, False otherwise.
    """
    return system_helpers.find_in_processes(CONSTANTS['executables']['league']['game'])

def league_client_running() -> bool:
    """Checks if the league client is already running.

    Returns:
        bool: True if the client is running, False otherwise.
    """
    return system_helpers.find_in_processes(CONSTANTS['executables']['league']['client']) and \
            system_helpers.find_in_processes(CONSTANTS['executables']['league']['client_ux'])

def parse_task_kill_text(result: subprocess.CompletedProcess[str]) -> None:
    """Parses the task kill text to log the result.

    Args:
        result (subprocess.CompletedProcess[str]): the return value of the subprocess run.
    """
    if 'not found.' in result.stderr:
        logging.debug(F"{result.args[-1]} was not running.")
    elif 'has been terminated.' in result.stdout:
        logging.debug(F"{result.args[-1]} has been terminated.")
    else:
        logging.warning(F"An unknown exception ocurred attempting to end {result.args[-1]}")
        logging.debug(result)

def restart_league_client() -> None:
    """Restarts the league client."""
    logging.debug("Killing League Client!")
    result = subprocess.run(["taskkill", "/f", "/im", CONSTANTS['processes']['client']], check=False, capture_output=True, text=True)
    parse_task_kill_text(result)
    result = subprocess.run(["taskkill", "/f", "/im", CONSTANTS['processes']['client_ux']], check=False, capture_output=True, text=True)
    parse_task_kill_text(result)
    time.sleep(1)
    subprocess.run(CONSTANTS['executables']['league']['client'], check=True)
    time.sleep(3)

def restart_league_if_not_running() -> bool:
    """Restarts the league client if it is not already running.

    Returns:
        bool: True if the league client was restarted, False otherwise.
    """
    if not league_client_running():
        logging.debug("League client not detected, restarting!")
        restart_league_client()
        return True
    return False

def toggle_pause() -> None:
    """Toggles whether the bots logic evaluation should pause.
    *Note:* This does not entirely stop the bot, but does stop various state changes that can be annoying if you're trying to manually interact with it.
    """
    global PAUSE_LOGIC
    logging.debug(f'alt+p pressed, toggling pause from {PAUSE_LOGIC} to {not PAUSE_LOGIC}')
    PAUSE_LOGIC = not PAUSE_LOGIC
    if PAUSE_LOGIC:
        logging.info("Bot now paused, remember to unpause to continue botting!")
    else:
        logging.info("Bot playing again!")


def is_in_queue() -> bool:
    """Checks if the League client is currently in queue / searching for a game.

    Returns:
        bool: True if the client is in queue, False otherwise.
    """
    return onscreen(CONSTANTS['client']['in_queue']['base']) or onscreen(CONSTANTS['client']['in_queue']['overshadowed'])


def is_in_tft_lobby() -> bool:
    """Checks if the League client is currently in the TFT lobby.

    Returns:
        bool: True if the client is in the TFT lobby, False otherwise.
    """
    return onscreen(CONSTANTS['tft_logo']['base']) or onscreen(CONSTANTS['tft_logo']['overshadowed'])


def find_match() -> None:
    """Begin actually finding a match, bringing the League client to the forefront/focus and dismissing any interruptions."""
    counter = 0
    while is_in_tft_lobby() and not check_if_client_error():
        bring_league_client_to_forefront()
        dismiss_interruptions()
        find_match_click_success = click_to_middle_multiple(find_match_images, conditional_func=is_in_queue, delay=0.2)
        logging.debug(f"Clicking find match success: {find_match_click_success}")
        time.sleep(1)
        while not onscreen(CONSTANTS['game']['loading']) and not onscreen(CONSTANTS['game']['round']['1-1']) and is_in_queue():
            click_to_middle(CONSTANTS['client']['in_queue']['accept'])
            time.sleep(1)

            if not is_in_queue():
                counter = counter + 1

            if counter > 60:
                logging.info("Was not in queue for 60 seconds, aborting")
                break

        counter = counter + 1
        if counter > 60:
            logging.info("An exception occurred while finding match")
            break

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
            break
    return league_game_already_running()

# Start between match logic
def queue() -> None:
    """Begin finding a match -- the start of the repeating game logic, dismissing any interruptions and bringing the League client to the forefront/focus."""
    # Queue search loop
    while True:
        if PAUSE_LOGIC:
            time.sleep(5)
        else:
            game_launched = False
            if restart_league_if_not_running():
                continue
            # Not already in queue
            bring_league_client_to_forefront()
            dismiss_interruptions()
            if not is_in_queue():
                if is_in_tft_lobby():
                    logging.info("TFT lobby detected, finding match")
                    find_match()
                    game_launched = True
                elif league_game_already_running():
                    logging.info("Already in game!")
                    game_launched = True
                    break
                # Post-match screen
                elif check_if_post_game():
                    match_complete()
                else:
                    logging.warning("TFT lobby not detected!")
                    restart_league_client()
                    continue

            if game_launched:
                wait_for_league_running()

            if league_game_already_running() and onscreen(CONSTANTS['game']['loading']):
                logging.info("Loading!")
                break
            if onscreen(CONSTANTS['game']['gamelogic']['timer_1']) or league_game_already_running():
                logging.info("Already in game :O!")
                break
    loading_match()


def loading_match() -> None:
    """Attempt to wait for the match to load, bringing the League game to the forefront/focus.
    After some time, if the game has not been detected as starting, it moves on anyways.
    """
    counter = 0
    logging.info("Match Loading!")
    bring_league_game_to_forefront()

    while not onscreen(CONSTANTS['game']['round']['1-1']) and not onscreen(CONSTANTS['game']['gamelogic']['timer_1']):
        time.sleep(0.5)
        # In case the client isn't already running, try waiting for it
        wait_for_league_running()
        bring_league_game_to_forefront()
        if counter > 60:
            logging.warning("Did not detect game start, continuing anyways 😬")
        counter = counter + 1

    logging.info("Match starting!")
    start_match()


def start_match() -> None:
    """Do initial first round pathing to pick the first champ."""
    while onscreen(CONSTANTS['game']['round']['1-1']):
        shared_draft_pathing()
    logging.info("In the match now!")
    main_game_loop()


def shared_draft_pathing() -> None:
    """Navigate counter-clockwise in a diamond to help ensure a champ is picked up."""
    auto.moveTo(946, 315)
    click_right()
    time.sleep(3)
    auto.moveTo(700, 450)
    click_right()
    time.sleep(3)
    auto.moveTo(950, 675)
    click_right()
    time.sleep(3)
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
        for i in wanted_traits:
            if onscreen(i):
                click_to_middle(i)
                time.sleep(0.5)
            else:
                return

def click_ok_message() -> None:
    """Click the message OK button"""
    click_to_middle(CONSTANTS['client']['messages']['buttons']['message_ok'])

def click_exit_message() -> None:
    """Click the message Exit button"""
    click_to_middle(CONSTANTS['client']['messages']['buttons']['message_exit'])

def wait_for_internet() -> None:
    """Delay indefinitely until an internet is detected."""
    while not system_helpers.have_internet():
        logging.warning("Internet is not up, will retry in 60 seconds")
        time.sleep(60)

def check_if_client_error() -> bool:
    """Check if any client error is detected.
    If any are detected, the League client is restarted.

    Returns:
        bool: True if a client error message was detected.
    """
    if onscreen(CONSTANTS['client']['messages']['session_expired']):
        logging.info("Session expired!")
        click_ok_message()
        time.sleep(5)
        restart_league_client()
        return True
    if onscreen(CONSTANTS['client']['messages']['failed_to_reconnect']):
        logging.info("Failed to reconnect!")
        click_exit_message()
        time.sleep(5)
        wait_for_internet()
        restart_league_client()
        return True
    if onscreen(CONSTANTS['client']['messages']['login_servers_down']):
        logging.info("Login servers down!")
        click_exit_message()
        time.sleep(5)
        wait_for_internet()
        restart_league_client()
        return True
    return False

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
    if not league_game_already_running() and not attempt_reconnect_to_existing_game():
        return True
    if check_if_client_error():
        return True
    if onscreen(CONSTANTS['client']['death']):
        logging.info("Death detected")
        click_to_middle(CONSTANTS['client']['death'])
        time.sleep(5)
    if onscreen_multiple_any(exit_now_images):
        logging.info("End of game detected")
        exit_now_bool = click_to_middle_multiple(exit_now_images, conditional_func=exit_now_conditional, delay=1.5)
        logging.debug(f"Exit now clicking success: {exit_now_bool}")
        time.sleep(5)
    return onscreen(CONSTANTS['client']['post_game']['play_again']) or \
                onscreen(CONSTANTS['client']['pre_match']['quick_play']) or \
                onscreen_multiple_any(skip_waiting_for_stats_images)


def attempt_reconnect_to_existing_game() -> bool:
    """If there is a Reconnect button on screen in the client, attempt to reconnect.

    Returns:
        bool: True if a reconnect is attempted, False otherwise.
    """
    if onscreen(CONSTANTS['client']['reconnect']):
        logging.info("Reconnecting!")
        time.sleep(0.5)
        click_to_middle(CONSTANTS['client']['reconnect'])
        return True
    return False


def check_if_post_game() -> bool:
    """Checks to see if the game was interrupted.

    Returns:
        bool: True if the game was complete or a reconnection attempt is made, False otherwise.
    """
    if check_if_game_complete():
        return True
    return attempt_reconnect_to_existing_game()


def check_if_gold_at_least(num: int) -> bool:
    """Check if the gold on screen is at least the provided amount

    Args:
        num (int): The value to check if the gold is at least.

    Returns:
        bool: True if the value is >= `num`, False otherwise.
    """
    logging.debug(f"Looking for at least {num} gold")
    for i in range(num + 1):
        try:
            if onscreen_region_numLoop(CONSTANTS['game']['gold'][f"{i}"], 0.1, 5, 780, 850, 970, 920, 0.9):
                logging.debug(f"Found {i} gold")
                if i == num:
                    logging.debug("Correct")
                    return True
                logging.debug("Incorrect")
                return False
        except Exception:
            logging.debug(f"Exception finding {i} gold, we possibly don't have the value as a file")
            # We don't have this gold as a file
            return True
    return True

def main_game_loop() -> None: #pylint: disable=too-many-branches
    """The main in-game loop.

    Skips 5 second increments if a pause logic request is made, repeating until toggled or an event triggers an early exit.

    Support for forfeiting early does exist but is rarely tested as the main author does not use this feature.
    """
    should_exit = False
    while should_exit is False:
        if PAUSE_LOGIC:
            time.sleep(5)
        else:
            # Handle recurring round logic
            # Treasure dragon, dont reroll just take it
            if onscreen(CONSTANTS['game']['gamelogic']['take_all']):
                click_to_middle(CONSTANTS['game']['gamelogic']['take_all'])
                time.sleep(1)
                continue
            # Free champ round
            if not onscreen(CONSTANTS['game']['round']['1-'], 0.9) and onscreen(CONSTANTS['game']['round']['-4'], 0.9):
                logging.info("Round X-4, draft detected")
                shared_draft_pathing()
                continue
            if onscreen(CONSTANTS['game']['round']['1-'], 0.9) or onscreen(CONSTANTS['game']['round']['2-'], 0.9):
                buy(3)
            # If round > 2, attempt re-rolls
            if check_if_gold_at_least(4) and onscreen(CONSTANTS['game']['gamelogic']['xp_buy']):
                click_to_middle(CONSTANTS['game']['gamelogic']['xp_buy'])
                time.sleep(0.2)
                continue
            if not onscreen(CONSTANTS['game']['round']['1-'], 0.9) and not onscreen(CONSTANTS['game']['round']['2-'], 0.9):
                if check_if_gold_at_least(2) and onscreen(CONSTANTS['game']['gamelogic']['reroll']):
                    click_to_middle(CONSTANTS['game']['gamelogic']['reroll'])

            time.sleep(0.5)

        if check_if_post_game():
            match_complete()
            break

        if FF_EARLY:
            # Change the round to end the round early at a different time
            if not onscreen(CONSTANTS["game"]["1-"], 0.9) and not onscreen(CONSTANTS["game"]["2-", 0.9]):
                if not onscreen("./captures/3-1.png", 0.9):
                    logging.info("Surrendering now!")
                    surrender()
                    break


def end_match() -> None:
    """End of TFT game logic.

    Loops to ensure the various end-of-match scenarios are accounte for to help ensure we make it back to the next find match button.

    Will dismiss various interruptions and screen such as 'waiting for stats' or 'play again'.
    """
    # added a main loop for the end match function to ensure you make it to the find match button.
    while not onscreen_multiple_any(find_match_images):
        bring_league_client_to_forefront()
        if check_if_client_error() or not league_client_running():
            return
        dismiss_interruptions()
        if onscreen_multiple_any(skip_waiting_for_stats_images):
            logging.info("Skipping waiting for stats")
            click_to_middle_multiple(skip_waiting_for_stats_images)
            time.sleep(3)
        if onscreen(CONSTANTS['client']['post_game']['play_again']):
            logging.info("Attempting to play again")
            bring_league_client_to_forefront()
            click_to_middle(CONSTANTS['client']['post_game']['play_again'], delay=0.5)
            time.sleep(3)
        if onscreen(CONSTANTS['client']['pre_match']['quick_play']):
            logging.info("Attempting to quick play")
            click_to_middle(CONSTANTS['client']['pre_match']['quick_play'])
            time.sleep(10)
        if not onscreen_multiple_any(find_match_images) and onscreen(CONSTANTS['client']['tabs']['tft']['unselected'], precision=0.9):
            logging.info("Detected that TFT tab is not selected, attempting ot select")
            click_to_middle(CONSTANTS['client']['tabs']['tft']['unselected'])
            time.sleep(3)

def dismiss_interruptions() -> None:
    """Dismisses any 'earned key fragment' and 'mission completion' messages.

    If a mission completion is detected, it will attempt to take a screenshot of the message.
    """
    if onscreen_multiple_any(key_fragment_images, 0.7):
        logging.info("Dismissing key fragment")
        click_to_middle_multiple(key_fragment_images, 0.7)
        time.sleep(0.5)
    while onscreen(CONSTANTS['client']['post_game']['missions_ok']):
        logging.info("Dismissing mission")
        try:
            localtime = time.localtime()    # added for printing time
            current_time = time.strftime("%H%M%S", localtime) #for the changing file name
            Path(CONSTANTS["client"]["screenshot_location"]).mkdir(parents=True, exist_ok=True)
            my_screenshot = auto.screenshot()
            my_screenshot.save(rf'{CONSTANTS["client"]["screenshot_location"]}/{current_time}.png')
            time.sleep(0.5)
            logging.info("Screenshot of mission saved")
            click_to_middle(CONSTANTS['client']['post_game']['missions_ok'])
        except Exception as exception:
            logging.critical(exception)
        time.sleep(1)

def match_complete() -> None:
    """Print a log timer to update the time passed and number of games completed (rough estimation), and begin the end of match logic."""
    print_timer()
    logging.info("Match complete! Cleaning up and restarting")
    time.sleep(1)
    end_match()


def surrender() -> None:
    """Attempt to surrender.

    *Notice:* The main author does not use this often, so this is not tested between most updates.
    """
    counter = 0
    surrenderwait = random.randint(100, 150)
    logging.info(f'Waiting {surrenderwait} seconds ({surrenderwait / 60 } minutes) to surrender')
    time.sleep(surrenderwait)
    logging.info("Starting surrender")
    click_to_middle(CONSTANTS['game']['settings'])

    while not onscreen(CONSTANTS['game']['surrender']['surrender_1']):
        # just in case it gets interrupted or misses
        click_to_middle(CONSTANTS['game']['settings'])
        time.sleep(1)
        counter = counter + 1
        if counter > 20:
            break
    counter = 0
    while not onscreen(CONSTANTS['game']['surrender']['surrender_2']):
        click_to_middle(CONSTANTS['game']['surrender']['surrender_1'])
        # added a check here for the rare case that the game ended before the surrender finished.
        if check_if_post_game():
            return
        counter = counter + 1
        if counter > 20:
            break

    time.sleep(1)
    click_to_middle(CONSTANTS['game']['surrender']['surrender_2'])
    time.sleep(10)
    end_match()
    time.sleep(5)

    logging.info("Surrender Complete")
    match_complete()


def print_timer() -> None:
    """Print a log timer to update the time passed and number of games completed (rough estimation)."""
    global END_TIMER, GAME_COUNT
    END_TIMER = time.time()
    GAME_COUNT += 1
    sec = (END_TIMER - START_TIMER)
    hours = sec // 3600
    sec = sec - hours*3600
    mins = sec // 60
    seconds = sec - mins*60
    gamecount_string = str(GAME_COUNT)

    logging.info("-------------------------------------")
    logging.info(f"Current Time = {datetime.now().strftime('%H:%M:%S')}")
    logging.info("-------------------------------------")
    logging.info("Game End")
    logging.info(f"Play Time : {int(float(hours))} Hour, {int(float(mins))} Min, {int(float(seconds))} Sec")
    logging.info(f"Gamecount : {gamecount_string}")
    logging.info("-------------------------------------")

def tft_bot_loop() -> None:
    """Main loop to ensure various errors don't unhinge/break the bot.
    Since the bot is able to reconnect and handle most errors, this should allow it to resume games in progress even if an 'uncaught exception' has occurred.
    """
    while True:
        try:
            queue()
        except AttributeError:
            logging.info("Not already in game, couldn't find game client on screen, looping")
            time.sleep(5)
            continue

def main():
    """Entrypoint function to initialize most of the code.

    Parses command line arguments, sets up console settings, logging, and kicks of the main bot loop.
    """
    global FF_EARLY, VERBOSE

    arg_parser = argparse.ArgumentParser(prog="TFT Bot")
    arg_parser.add_argument("--ffearly", action='store_true', help="If the game should be surrendered at first available time.")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity, mostly useful for debugging")
    parsed_args = arg_parser.parse_args()

    FF_EARLY = parsed_args.ffearly
    VERBOSE = parsed_args.verbose
    logging_handlers = [logging.StreamHandler()]
    if VERBOSE:
        logging_handlers.append(logging.FileHandler("debug.log"))

    if VERBOSE:
        logging.info("Will explain everything and be very verbose")
    else:
        logging.info("Will be quiet and not be very verbose")

    if FF_EARLY:
        logging.info("FF Early Specified - Will surrender at first available time")
    else:
        logging.info("FF Early Not Specified - Will play out games for their duration")

    system_helpers.disable_quickedit()
    os.system('color 0F')
    # Start auth + main script
    logging.info("Initial codebase by:")
    printy(r"""
    [c>] _____       _                            _   @
    [c>]|  __ \     | |                          | |  @
    [c>]| |  | | ___| |_ ___ _ __ __ _  ___ _ __ | |_ @
    [c>]| |  | |/ _ \ __/ _ \ '__/ _` |/ _ \ '_ \| __|@
    [c>]| |__| |  __/ ||  __/ | | (_| |  __/ | | | |_ @
    [c>]|_____/ \___|\__\___|_|  \__, |\___|_| |_|\__|@
    [c>]                          __/ |               @
    [c>]                         |___/                @
    """, "{k}")
    logging.info("Re-written by:")
    printy(r"""
    [c>]    __ __              __              __                __                  __  @
    [c>]   / //_/__  __ _____ / /__  __ _____ / /__ ___   _____ / /_   __  __ _____ / /__@
    [c>]  / ,<  / / / // ___// // / / // ___// //_// _ \ / ___// __ \ / / / // ___// //_/@
    [c>] / /| |/ /_/ // /   / // /_/ // /__ / ,<  /  __// /__ / / / // /_/ // /__ / ,<   @
    [c>]/_/ |_|\__, //_/   /_/ \__,_/ \___//_/|_| \___/ \___//_/ /_/ \__,_/ \___//_/|_|  @
    [c>]      /____/                                                                     @
    """, "{k}")
    os.system('color 0F')

    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    if not setup_logging(
            console_log_output="stdout",
            console_log_level="debug" if VERBOSE else "info",
            console_log_color=True,
            logfile_file=script_name + ".log",
            logfile_log_level="debug",
            logfile_log_color=False,
            log_line_template="%(color_on)s[%(created)d] [%(threadName)s] %(levelname)-8s || %(message)s%(color_off)s"
        ):
        print("Failed to set up logger, continue with caution!")
        if auto.confirm(title="TFT Auto Bot - Logging Setup Failure",
                text="Failed to set up logger, continue with caution!\n", buttons=['Proceed', 'Cancel']) == "Cancel":
            print("Startup aborted!")
            sys.exit(1)
    else:
        print("Logger setup success")

    logging.info("Welcome! \nPlease feel free to ask questions or contribute at https://github.com/Kyrluckechuck/tft-bot")
    if auto.confirm(title="TFT Auto Bot", text="Press Start when the bot should continue!\n", buttons=['Start', 'Cancel']) != 'Start':
        logging.critical("Intialization completed but aborting by user choice!")
        sys.exit(1)
    logging.info("Bot started, queuing up!")

    keyboard.add_hotkey('alt+p', lambda: toggle_pause()) #pylint: disable=unnecessary-lambda

    global START_TIMER
    START_TIMER = time.time()
    tft_bot_loop()


if __name__ == "__main__":
    sys.exit(main())
