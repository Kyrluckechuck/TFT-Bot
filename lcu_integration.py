import time

from loguru import logger
from psutil import Process
from psutil import process_iter
import requests

# Potentially make this configurable in the future
# to let the user select their preferred tft mode.
from requests import HTTPError
import urllib3

TFT_NORMAL_GAME_QUEUE_ID = 1090


# LCU logic taken from https://github.com/elliejs/Willump
# We want to implement a synchronous approach,
# so we are not using the library.
def get_lcu_process():
    for process in process_iter():
        if process.name() in {'LeagueClientUx.exe', 'LeagueClientUx'}:
            return process
    return None


def _get_lcu_commandline_arguments(lcu_process: Process):
    commandline_arguments = {}

    for commandline_argument in lcu_process.cmdline():
        if len(commandline_argument) > 0 and '=' in commandline_argument:
            key, value = commandline_argument[2:].split('=', 1)
            commandline_arguments[key] = value

    return commandline_arguments


class LCUIntegration:
    def __init__(self):
        self._session = None
        self._url = None
        self.install_directory = None

    def connect_to_lcu(self, wait_for_availability: bool = False) -> bool:
        logger.info("Waiting for the League client (~5m timeout)")
        lcu_process = get_lcu_process()

        timeout = 0
        while not lcu_process:
            if timeout >= 300:
                logger.warning(
                    "Couldn't find the League client within 5 minutes, exiting"
                )
                return False
            logger.debug(
                "Couldn't find LCUx process yet. Re-searching process list..."
            )
            time.sleep(1)
            lcu_process = get_lcu_process()
            timeout += 1

        logger.debug("LCUx process found")
        process_arguments = _get_lcu_commandline_arguments(lcu_process)
        self.install_directory = process_arguments["install-directory"]
        self._url = f"https://127.0.0.1:{process_arguments['app-port']}"
        _auth_key = process_arguments['remoting-auth-token']

        if self._session is not None:
            logger.debug(
                "LCU session already existed, closing it just to be safe."
            )
            self._session.close()

        self._session = requests.Session()
        self._session.auth = ("riot", _auth_key)
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        # TODO Do proper SSL integration
        self._session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        logger.info(
            "League client found, trying to connect to it (~60s timeout)"
        )
        timeout = 0
        while True:
            if timeout >= 60:
                logger.warning(
                    "Couldn't connect to the League client, exiting"
                )
                return False

            try:
                response = self._session.get(
                    url=f"{self._url}/riotclient/ux-state"
                )
                response.raise_for_status()
                logger.debug("Connected to LCUx server.")
                break
            except requests.exceptions.RequestException:
                logger.debug(
                    "Can't connect to LCUx server. Retrying..."
                )
                time.sleep(1)
                timeout += 1

        logger.info("Successfully connected to the League client")

        if wait_for_availability:
            logger.info(
                "Waiting for client availability (~120s timeout)"
            )
            timeout = 0
            while timeout < 120:
                availability_response = self._session.get(
                    url=f"{self._url}/lol-gameflow/v1/availability"
                )
                if (
                        availability_response.status_code == 200
                        and availability_response.json()["isAvailable"]
                ):
                    logger.info("Client available, queue logic should start")
                    return True
                time.sleep(1)
                timeout += 1
            logger.error("Client did not become available. Exiting.")
            return False

        return True

    def get_installation_directory(self) -> str | None:
        return self.install_directory

    def in_lobby(self) -> bool:
        get_lobby_response = self._session.get(
            f"{self._url}/lol-lobby/v2/lobby",
        )

        try:
            get_lobby_response.raise_for_status()
        except HTTPError:
            return False

        return (
                get_lobby_response.json()["gameConfig"]["queueId"]
                == TFT_NORMAL_GAME_QUEUE_ID
        )

    def create_lobby(self) -> bool:
        logger.info("Creating a TFT lobby")
        create_lobby_response = self._session.post(
            f"{self._url}/lol-lobby/v2/lobby",
            json={
                "queueId": TFT_NORMAL_GAME_QUEUE_ID
            }
        )

        return create_lobby_response.status_code == 200

    def delete_lobby(self):
        logger.info("Closing the lobby because it seems we got stuck")
        self._session.delete(
            f"{self._url}/lol-lobby/v2/lobby",
        )

    def start_queue(self) -> bool:
        logger.info("Starting the match finding queue")
        start_queue_response = self._session.post(
            f"{self._url}/lol-lobby/v2/lobby/matchmaking/search",
        )
        return start_queue_response.status_code == 204

    def in_queue(self) -> bool:
        logger.debug("Checking if we are already in a queue")
        get_queue_response = self._session.get(
            f"{self._url}/lol-lobby/v2/lobby/matchmaking/search-state",
        )

        if get_queue_response.status_code != 200:
            return False

        return get_queue_response.json()["searchState"] in {
            "Searching", "Found"
        }

    def found_queue(self) -> bool:
        logger.debug("Checking if we have found a match")
        get_queue_response = self._session.get(
            f"{self._url}/lol-lobby/v2/lobby/matchmaking/search-state",
        )

        if get_queue_response.status_code != 200:
            return False

        return get_queue_response.json()["searchState"] == "Found"

    def queue_accepted(self):
        logger.debug("Checking if we already accepted the queue")
        ready_check_state = self._session.get(
            f"{self._url}/lol-matchmaking/v1/ready-check"
        )

        if ready_check_state.status_code != 200:
            return False

        return ready_check_state.json()["playerResponse"] == "Accepted"

    def accept_queue(self):
        logger.info("Match ready, accepting the queue")
        self._session.post(
            f"{self._url}/lol-matchmaking/v1/ready-check/accept"
        )

    def in_game(self) -> bool:
        logger.debug("Checking if we are in a game")
        try:
            session_response = self._session.get(
                f"{self._url}/lol-gameflow/v1/session",
            )
        except requests.exceptions.ConnectionError:
            self.connect_to_lcu()
            return self.in_game()

        if session_response.status_code != 200:
            return False

        return session_response.json()["phase"] in {
            "ChampSelect", "GameStart", "InProgress", "Reconnect"
        }

    def should_reconnect(self) -> bool:
        logger.debug("Checking if we should reconnect")
        session_response = self._session.get(
            f"{self._url}/lol-gameflow/v1/session",
        )

        if session_response.status_code != 200:
            return False

        return session_response.json()["phase"] == "Reconnect"
