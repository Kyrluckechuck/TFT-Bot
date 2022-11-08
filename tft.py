import time
import random
import keyboard
import os
import subprocess
import sys
import logging

import argparse
import pkg_resources
import pyautogui as auto
from printy import printy
from datetime import datetime

from constants import CONSTANTS, find_match_images, exit_now_images, skip_waiting_for_stats_images
import system_helpers
from logging_helper import setup_logging
from screen_helpers import onscreen, onscreen_multiple_any, onscreen_region_numLoop
from click_helpers import click_right, click_to_middle_multiple, click_to_middle, click_to_middle_multiple


auto.FAILSAFE = False
gamecount = -1
endtimer = time.time()
pauselogic = False
FF_EARLY = False
VERBOSE = False


def bring_league_client_to_forefront() -> None:
    try:
        system_helpers.bring_window_to_forefront("League of Legends", CONSTANTS['executables']['league']['client_ux'])
    except Exception:
        logging.warning("Failed to bring League client to forefront, this should be non-fatal so let's continue")

def bring_league_game_to_forefront() -> None:
    try:
        system_helpers.bring_window_to_forefront("League of Legends", CONSTANTS['executables']['league']['game'])
    except Exception:
        logging.warning("Failed to bring League game to forefront, this should be non-fatal so let's continue")

def league_game_already_running() -> bool:
    return system_helpers.find_in_processes(CONSTANTS['executables']['league']['game'])

def league_client_running() -> bool:
    return system_helpers.find_in_processes(CONSTANTS['executables']['league']['client']) and system_helpers.find_in_processes(CONSTANTS['executables']['league']['client_ux'])

def parse_task_kill_text(result: subprocess.CompletedProcess[str]) -> None:
    if 'not found.' in result.stderr:
        logging.debug(F"{result.args[-1]} was not running.")
    elif 'has been terminated.' in result.stdout:
        logging.debug(F"{result.args[-1]} has been terminated.")
    else:
        logging.warning(F"An unknown exception ocurred attempting to end {result.args[-1]}")
        logging.debug(result)

def restart_league_client() -> None:
    logging.debug("Killing League Client!")
    result = subprocess.run(["taskkill", "/f", "/im", CONSTANTS['processes']['client']], capture_output=True, text=True)
    parse_task_kill_text(result)
    result = subprocess.run(["taskkill", "/f", "/im", CONSTANTS['processes']['client_ux']], capture_output=True, text=True)
    parse_task_kill_text(result)
    time.sleep(3)
    subprocess.run(CONSTANTS['executables']['league']['client'])
    time.sleep(5)

def restart_league_if_not_running() -> bool:
    if not league_client_running():
        logging.debug("League client not detected, restarting!")
        restart_league_client()
        return True
    return False

def toggle_pause() -> None:
    global pauselogic
    logging.debug(f'alt+p pressed, toggling pause from {pauselogic} to {not pauselogic}')
    pauselogic = not pauselogic
    if pauselogic:
        logging.info("Bot now paused, remember to unpause to continue botting!")
    else:
        logging.info("Bot playing again!")


def is_in_queue() -> bool:
    return onscreen(CONSTANTS['client']['in_queue']['base']) or onscreen(CONSTANTS['client']['in_queue']['overshadowed'])


def is_in_tft_lobby() -> bool:
    return onscreen(CONSTANTS['tft_logo']['base']) or onscreen(CONSTANTS['tft_logo']['overshadowed'])


def find_match() -> None:
    counter = 0
    while is_in_tft_lobby() and not check_if_client_error():
        bring_league_client_to_forefront()
        find_match_click_success = click_to_middle_multiple(find_match_images, conditional_func=is_in_queue, delay=0.2)
        logging.debug(f"Clicking find match success: {find_match_click_success}")
        time.sleep(1)
        while not onscreen(CONSTANTS['game']['loading']) and not onscreen(CONSTANTS['game']['round']['1-1']) and is_in_queue():
            click_to_middle(CONSTANTS['client']['in_queue']['accept'])
            time.sleep(1)

            if not is_in_queue():
                counter = counter + 1

            if (counter > 60):
                logging.info("Was not in queue for 60 seconds, aborting")
                break

        counter = counter + 1
        if (counter > 60):
            logging.info("An exception occurred while finding match")
            break

def wait_for_league_running() -> bool:
    counter = 0
    while not league_game_already_running():
        counter = counter + 1
        time.sleep(0.5)
        if counter > 60:
            break
    return league_game_already_running()

# Start between match logic
def queue() -> None:
    # Queue search loop
    while True:
        if pauselogic:
            time.sleep(5)
        else:
            game_launched = False
            if restart_league_if_not_running():
                continue
            # Not already in queue
            bring_league_client_to_forefront()
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
            elif onscreen(CONSTANTS['game']['gamelogic']['timer_1']) or league_game_already_running():
                logging.info("Already in game :O!")
                break
    loading_match()


def loading_match() -> None:
    counter = 0
    logging.info("Match Loading!")
    bring_league_game_to_forefront()

    while not onscreen(CONSTANTS['game']['round']['1-1']) and not onscreen(CONSTANTS['game']['gamelogic']['timer_1']):
        time.sleep(0.5)
        # In case the client isn't already running, try waiting for it
        wait_for_league_running()
        bring_league_game_to_forefront()
        if counter > 60:
            logging.warn("Did not detect game start, continuing anyways 😬")
        counter = counter + 1

    logging.info("Match starting!")
    start_match()


def start_match() -> None:
    while onscreen(CONSTANTS['game']['round']['1-1']):
        shared_draft_pathing()
    logging.info("In the match now!")
    main_game_loop()


def shared_draft_pathing() -> None:
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

wanted_traits = [
    CONSTANTS['game']['trait']['bruiser'],
    CONSTANTS['game']['trait']['mage'],
    CONSTANTS['game']['trait']['jade']
]

def buy(iterations) -> None:
    for i in range(iterations):
        if not check_if_gold_at_least(1):
            return
        for i in wanted_traits:
            if onscreen(i):
                click_to_middle(i)
                time.sleep(0.5)
            else:
                return

def check_if_client_error() -> bool:
    if onscreen(CONSTANTS['client']['messages']['session_expired']):
        logging.info("Session expired!")
        click_to_middle(CONSTANTS['client']['messages']['buttons']['message_ok'])
        time.sleep(5)
        restart_league_client()
        return True
    if onscreen(CONSTANTS['client']['messages']['failed_to_reconnect']):
        logging.info("Failed to reconnect!")
        click_to_middle(CONSTANTS['client']['messages']['buttons']['message_exit'])
        time.sleep(3)
        while not system_helpers.have_internet():
            logging.info("Internet is not up, will retry in 60 seconds")
            time.sleep(60)
        restart_league_client()
        return True
    return False

def exit_now_conditional() -> bool:
    return not league_game_already_running()

def check_if_game_complete() -> bool:
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
    return onscreen(CONSTANTS['client']['post_game']['play_again']) or onscreen(CONSTANTS['client']['pre_match']['quick_play']) or onscreen_multiple_any(skip_waiting_for_stats_images)


def attempt_reconnect_to_existing_game() -> bool:
    if onscreen(CONSTANTS['client']['reconnect']):
        logging.info("Reconnecting!")
        time.sleep(0.5)
        click_to_middle(CONSTANTS['client']['reconnect'])
        return True
    return False


def check_if_post_game() -> bool:  # checks to see if game was interrupted
    if check_if_game_complete():
        return True
    return attempt_reconnect_to_existing_game()


def check_if_gold_at_least(num) -> bool:
    logging.debug(f"Looking for at least {num} gold")
    for i in range(num + 1):
        # logging.info(f"Checking for {i} gold")
        try:
            if onscreen_region_numLoop(CONSTANTS['game']['gold'][f"{i}"], 0.1, 5, 780, 850, 970, 920, 0.9):
                logging.debug(f"Found {i} gold")
                if (i == num):
                    logging.debug("Correct")
                    return True
                else:
                    logging.debug("Incorrect")
                    return False
        except Exception:
            logging.debug(f"Exception finding {i} gold")
            # We don't have this gold as a file
            return True
    return True


def main_game_loop() -> None:
    global FF_EARLY
    exit = False
    while exit == False:
        if pauselogic:
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
            elif onscreen(CONSTANTS['game']['round']['1-'], 0.9) or onscreen(CONSTANTS['game']['round']['2-'], 0.9):
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
            # change this if you want to surrender at a different stage, also the image recognition struggles with 5 being it sees it as 3 so i had to do 6 as that's seen as a 5
            if not onscreen(CONSTANTS["game"]["1-"], 0.9) and not onscreen(CONSTANTS["game"]["2-", 0.9]):
                if not onscreen("./captures/3-1.png", 0.9):
                    logging.info("Surrendering now!")
                    surrender()
                    break


def end_match() -> None:
    # added a main loop for the end match function to ensure you make it to the find match button.
    while not onscreen_multiple_any(find_match_images):
        bring_league_client_to_forefront()
        if check_if_client_error():
            return
        while onscreen(CONSTANTS['client']['post_game']['missions_ok']):
            logging.info("Dismissing mission")
            #screenshot if you have an "ok" button
            t = time.localtime()    # added for printing time
            current_time = time.strftime("%H%M%S", t) #for the changing file name
            myScreenshot = auto.screenshot()
            myScreenshot.save(rf'{CONSTANTS["client"]["screenshot_location"]}/{current_time}.png')
            time.sleep(2)
            logging.info("Screenshot of mission saved")
            click_to_middle(CONSTANTS['client']['post_game']['missions_ok'])
            time.sleep(3)
        if onscreen_multiple_any(skip_waiting_for_stats_images):
            logging.info("Skipping waiting for stats")
            click_to_middle_multiple(skip_waiting_for_stats_images)
            time.sleep(10)
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


def match_complete() -> None:
    print_timer()
    logging.info("Match complete! Cleaning up and restarting")
    time.sleep(1)
    end_match()


def surrender() -> None:
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
        if (counter > 20):
            break
    counter = 0
    while not onscreen(CONSTANTS['game']['surrender']['surrender_2']):
        click_to_middle(CONSTANTS['game']['surrender']['surrender_1'])
        # added a check here for the rare case that the game ended before the surrender finished.
        if check_if_post_game():
            return
        counter = counter + 1
        if (counter > 20):
            break

    time.sleep(1)
    click_to_middle(CONSTANTS['game']['surrender']['surrender_2'])
    time.sleep(10)
    end_match()
    time.sleep(5)

    logging.info("Surrender Complete")
    match_complete()


def print_timer() -> None:
    global endtimer, gamecount
    endtimer = time.time()
    gamecount += 1
    sec = (endtimer - starttimer)
    hours = sec // 3600
    sec = sec - hours*3600
    mu = sec // 60
    ss = sec - mu*60
    gamecount_string = str(gamecount)

    logging.info("-------------------------------------")
    logging.info(f"Current Time = {datetime.now().strftime('%H:%M:%S')}")
    logging.info("-------------------------------------")
    logging.info("Game End")
    logging.info(f"Play Time : {int(float(hours))} Hour, {int(float(mu))} Min, {int(float(ss))} Sec")
    logging.info(f"Gamecount : {gamecount_string}")
    logging.info("-------------------------------------")
# End main process


def tft_bot_loop() -> None:
    while True:
        try:
            queue()
        except AttributeError:
            logging.info("Not already in game, couldn't find game client on screen, looping")
            time.sleep(5)
            continue


def main():
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
            console_log_level="debug" if VERBOSE else "warning",
            console_log_color=True,
            logfile_file=script_name + ".log",
            logfile_log_level="debug",
            logfile_log_color=False,
            log_line_template="%(color_on)s[%(created)d] [%(threadName)s] %(levelname)-8s || %(message)s%(color_off)s"
        ):
        print("Failed to set up logger, continue with caution!")
        if (auto.alert("Failed to set up logger, continue with caution!\n", buttons=['Proceed', 'Cancel']) == "Cancel"):
            return 1
    else:
        print("Logger setup success")

    logging.info(f"Welcome! \nPlease feel free to ask questions or contribute at https://github.com/Kyrluckechuck/tft-bot")
    auto.alert("Press OK when you're in a TFT lobby!\n")
    logging.info("Bot started, queuing up!")

    keyboard.add_hotkey('alt+p', lambda: toggle_pause())

    global starttimer
    starttimer = time.time()
    tft_bot_loop()


if (__name__ == "__main__"):
    sys.exit(main())
