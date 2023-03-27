import asyncio

from loguru import logger
from willump import Willump
from willump.proc_utils import find_LCU_process
from willump.proc_utils import parse_cmdline_args

_willump = Willump()
# Potentially make this configurable in the future
# to let the user select their preferred tft mode.
TFT_NORMAL_GAME_QUEUE_ID = 1090


async def start_willump() -> None:
    logger.info(
        "Attempting to connect to League client, "
        "please start it if you haven't yet..."
    )
    # Start up code taken from
    # https://github.com/elliejs/Willump/blob/main/willump/willump.py
    _willump.rest_alive = False

    lcu_process = find_LCU_process()
    while not lcu_process:
        logger.debug(
            "Couldn't find LCUx process yet. Re-searching process list..."
        )
        await asyncio.sleep(0.5)
        lcu_process = find_LCU_process()

    logger.debug("Found LCUx process " + lcu_process.name())
    process_args = parse_cmdline_args(lcu_process.cmdline())
    _willump._port = int(process_args['app-port'])
    _willump._auth_key = process_args['remoting-auth-token']

    _willump.start_rest()

    while True:
        try:
            resp = await _willump.request('get', '/riotclient/ux-state')
            if resp.status == 200:
                logger.debug(
                    "Connected to LCUx server."
                )
            else:
                logger.debug(
                    "Connected to LCUx https server, "
                    "but got an invalid response for a known uri. "
                    f"Response status code: {resp.status}"
                )
            break
        except Exception:
            logger.debug(
                "Can't connect to LCUx server. Retrying..."
            )
            await asyncio.sleep(0.5)
    logger.info("Successfully connected to the League client.")


async def is_in_lobby() -> bool:
    logger.debug("Checking if we are already in a lobby...")
    get_lobby_response = await _willump.request(
        "GET",
        "/lol-lobby/v2/lobby",
    )

    if get_lobby_response.status != 200:
        return False

    get_lobby_response_data = await get_lobby_response.json()
    return (
            get_lobby_response_data["gameConfig"]["queueId"]
            == TFT_NORMAL_GAME_QUEUE_ID
    )


async def create_lobby(check_if_post_game) -> bool:
    tft_lobby_data = {
        "queueId": TFT_NORMAL_GAME_QUEUE_ID
    }

    create_lobby_response = await _willump.request(
        "POST",
        "/lol-lobby/v2/lobby",
        data=tft_lobby_data
    )
    if create_lobby_response.status == 200:
        logger.info("Created a TFT lobby.")
        return True
    else:
        logger.warning(
            "There was an issue creating a TFT lobby. Checking post-game..."
        )
        await check_if_post_game()
        return False


async def start_queue() -> bool:
    logger.info("Starting the queue.")
    start_queue_response = await _willump.request(
        "POST",
        "/lol-lobby/v2/lobby/matchmaking/search",
    )
    return start_queue_response.status == 204


async def is_in_queue() -> bool:
    logger.debug("Checking if we are already in a queue...")
    get_queue_response = await _willump.request(
        "GET",
        "/lol-lobby/v2/lobby/matchmaking/search-state",
    )

    if get_queue_response.status != 200:
        return False

    get_queue_response_data = await get_queue_response.json()
    return get_queue_response_data["searchState"] in {"Searching", "Found"}


async def has_found_queue() -> bool:
    logger.debug("Checking if we have found a match...")
    get_queue_response = await _willump.request(
        "GET",
        "/lol-lobby/v2/lobby/matchmaking/search-state",
    )

    if get_queue_response.status != 200:
        return False

    get_queue_response_data = await get_queue_response.json()
    return get_queue_response_data["searchState"] == "Found"


async def accept_queue():
    logger.debug("Accepting the queue.")
    await _willump.request(
        "POST",
        "/lol-matchmaking/v1/ready-check/accept"
    )


async def is_in_game() -> bool:
    logger.debug("Checking if we are in a game...")
    session_response = await _willump.request(
        "GET",
        "/lol-gameflow/v1/session",
    )

    if session_response.status != 200:
        return False

    session_response_data = await session_response.json()
    return session_response_data["phase"] == "InProgress"
