"""
Integrations with the Rito API to have the most reliable data where possible.
"""
import time

from loguru import logger
from psutil import Process
from psutil import process_iter
import requests
from requests import HTTPError

from tft_bot import config

# Potentially make this configurable in the future
# to let the user select their preferred tft mode.
TFT_NORMAL_GAME_QUEUE_ID = 1090


# LCU logic taken from https://github.com/elliejs/Willump
# We want to implement a synchronous approach,
# so we are not using the library.
def get_lcu_process():
    """
    Get the LeagueClientUx process, aka. the process of the League client.

    Returns:
        The process if found, else None.

    """
    for process in process_iter():
        if process.name() in {"LeagueClientUx.exe", "LeagueClientUx"}:
            return process
    return None


def _get_lcu_commandline_arguments(lcu_process: Process):
    """
    Get the commandline arguments of the LCU process.

    Args:
        lcu_process: The process to parse the arguments of, preferably taken from get_lcu_process().

    Returns:
        A dictionary of the arguments, parsed as key/value.

    """
    commandline_arguments = {}

    for commandline_argument in lcu_process.cmdline():
        if len(commandline_argument) > 0 and "=" in commandline_argument:
            key, value = commandline_argument[2:].split("=", 1)
            commandline_arguments[key] = value

    return commandline_arguments


def _http_error_wrapper(method, raise_and_catch: bool = True, **kwargs) -> requests.Response | None:
    """
    Wraps an HTTP method to catch various errors.

    Args:
        method: The HTTP method to call.
        raise_and_catch: Whether we should call raise_for_status and catch the exception, if there is one
        **kwargs: Any keyword arguments to pass to the method.

    Returns:
        The response or None if any exceptions were caught.

    """
    try:
        response: requests.Response = method(**kwargs)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return None

    if raise_and_catch:
        try:
            response.raise_for_status()
        except HTTPError:
            return None

    return response


class LCUIntegration:
    """
    Integrates the bot with League Client Update (LCU) API.
    Note that the API is allowed to use, but not officially supported by Rito.
    The endpoints we use are stable-ish, and we do not expect them to change soonTM.
    """

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        self._session.verify = "tft_bot/resources/riotgames_root_certificate.pem"
        self._url = None
        self.install_directory = None

    def connect_to_lcu(self, wait_for_availability: bool = False) -> bool:
        """
        Connect to the LCU client. Searches for the process and creates a session.
        Has the option to wait for the league client to report that it's ready.

        Args:
            wait_for_availability: Whether we should wait for the client to report that it's ready to open games.

        Returns:
            True if we succeeded in connecting, False if not.

        """
        league_client_timeout = config.get_timeout(config.Timeout.LEAGUE_CLIENT, 300)
        logger.info(f"Waiting for the League client (~{league_client_timeout}s timeout)")
        lcu_process = get_lcu_process()

        timeout = 0
        while not lcu_process:
            if timeout >= league_client_timeout:
                logger.warning(f"Couldn't find the League client within {league_client_timeout}s, exiting")
                return False
            logger.debug("Couldn't find LCUx process yet. Re-searching process list...")
            time.sleep(1)
            lcu_process = get_lcu_process()
            timeout += 1

        logger.debug("LCUx process found")
        process_arguments = _get_lcu_commandline_arguments(lcu_process)
        self.install_directory = process_arguments["install-directory"]
        self._url = f"https://127.0.0.1:{process_arguments['app-port']}"
        self._session.auth = ("riot", process_arguments["remoting-auth-token"])

        connect_timeout = config.get_timeout(config.Timeout.CLIENT_CONNECT, 60)
        logger.info(f"League client found, trying to connect to it (~{connect_timeout}s timeout)")
        timeout = 0
        while True:
            if timeout >= connect_timeout:
                logger.warning("Couldn't connect to the League client, exiting")
                return False

            try:
                response = self._session.get(url=f"{self._url}/riotclient/ux-state")
                response.raise_for_status()
                logger.debug("Connected to LCUx server.")
                break
            except requests.exceptions.RequestException:
                logger.debug("Can't connect to LCUx server. Retrying...")
                time.sleep(1)
                timeout += 1

        logger.info("Successfully connected to the League client")

        if wait_for_availability:
            availability_timeout = config.get_timeout(config.Timeout.CLIENT_AVAILABILITY, 120)
            logger.info(f"Waiting for client availability (~{availability_timeout}s timeout)")
            for _ in range(availability_timeout):
                availability_response = self._session.get(url=f"{self._url}/lol-gameflow/v1/availability")
                if availability_response.status_code == 200 and availability_response.json()["isAvailable"]:
                    logger.info("Client available, queue logic should start")
                    return True
                time.sleep(1)
            logger.error("Client did not become available. Exiting.")
            return False

        return True

    def get_installation_directory(self) -> str | None:
        """
        Get the League Of Legends installation directory, parsed from the LCU process arguments.
        Should only be called after connect_to_lcu().

        Returns:
            The installation directory as a string if found, else None.

        """
        return self.install_directory

    def in_lobby(self) -> bool:
        """
        Check if we are in a lobby, also checks if the lobby is of the type we want (TFT_NORMAL_GAME_QUEUE_ID).

        Returns:
            True if we are in a lobby of the type we want, False if not.

        """
        get_lobby_response = _http_error_wrapper(self._session.get, url=f"{self._url}/lol-lobby/v2/lobby")

        if not get_lobby_response:
            return False

        return get_lobby_response.json()["gameConfig"]["queueId"] == TFT_NORMAL_GAME_QUEUE_ID

    def create_lobby(self) -> bool:
        """
        Create a lobby of the type we want.

        Returns:
            True if we succeeded in creating it, False if not.

        """
        logger.info("Creating a TFT lobby")
        create_lobby_response = _http_error_wrapper(
            self._session.post, url=f"{self._url}/lol-lobby/v2/lobby", json={"queueId": TFT_NORMAL_GAME_QUEUE_ID}
        )

        return create_lobby_response is not None and create_lobby_response.status_code == 200

    def delete_lobby(self) -> None:
        """
        Forcefully closes the current lobby, useful for "Player is not ready" bugs etc.
        """
        logger.info("Closing the lobby because it seems we got stuck")
        _http_error_wrapper(self._session.delete, url=f"{self._url}/lol-lobby/v2/lobby")

    def start_queue(self) -> bool:
        """
        Start finding a match.

        Returns:
            True if we succeeded in starting the search, False if not.

        """
        logger.info("Starting the match finding queue")
        start_queue_response = _http_error_wrapper(
            self._session.post, url=f"{self._url}/lol-lobby/v2/lobby/matchmaking/search"
        )
        return start_queue_response is not None and start_queue_response.status_code == 204

    def in_queue(self) -> bool:
        """
        Checks if we are in a match finding queue.

        Returns:
            True if we are in a match finding queue, False if not.

        """
        logger.debug("Checking if we are already in a queue")
        get_queue_response = _http_error_wrapper(
            self._session.get, url=f"{self._url}/lol-lobby/v2/lobby/matchmaking/search-state"
        )

        return get_queue_response.status_code is not None and get_queue_response.json()["searchState"] in {
            "Searching",
            "Found",
        }

    def found_queue(self) -> bool:
        """
        Checks if we have found a match that we need to accept.

        Returns:
            True if we have found a match that we need to accept, False if not.

        """
        logger.debug("Checking if we have found a match")
        get_queue_response = _http_error_wrapper(
            self._session.get, url=f"{self._url}/lol-lobby/v2/lobby/matchmaking/search-state"
        )

        return get_queue_response is not None and get_queue_response.json()["searchState"] == "Found"

    def queue_accepted(self) -> bool:
        """
        Checks if we have accepted the match.

        Returns:
            True if we have accepted the match, False if not.

        """
        logger.debug("Checking if we already accepted the queue")
        ready_check_state = _http_error_wrapper(self._session.get, url=f"{self._url}/lol-matchmaking/v1/ready-check")

        return ready_check_state is not None and ready_check_state.json()["playerResponse"] == "Accepted"

    def accept_queue(self) -> None:
        """
        Accept the match.
        """
        logger.info("Match ready, accepting the queue")
        _http_error_wrapper(self._session.post, url=f"{self._url}/lol-matchmaking/v1/ready-check/accept")

    def in_game(self) -> bool:
        """
        Checks if we are in a game.

        Returns:
            True if we are in a game, False if not.

        """
        logger.debug("Checking if we are in a game")
        session_response = _http_error_wrapper(self._session.get, url=f"{self._url}/lol-gameflow/v1/session")

        return session_response is not None and session_response.json()["phase"] in {
            "ChampSelect",
            "GameStart",
            "InProgress",
            "Reconnect",
        }

    def should_reconnect(self) -> bool:
        """
        Checks if we should reconnect to an existing game.

        Returns:
            True if we need to reconnect, False if not.

        """
        logger.debug("Checking if we should reconnect")
        session_response = _http_error_wrapper(self._session.get, url=f"{self._url}/lol-gameflow/v1/session")

        return session_response is not None and session_response.json()["phase"] == "Reconnect"

    def reconnect(self) -> None:
        """
        Reconnect to a running game.
        """
        logger.debug("Reconnecting to game")
        _http_error_wrapper(self._session.post, url=f"{self._url}/lol-gameflow/v1/reconnect")

    def session_expired(self) -> bool:
        """
        Check if the session is expired.

        Returns:
            True if it is expired, False if not.

        """
        logger.debug("Checking if our login session is expired")
        session_response = _http_error_wrapper(self._session.get, url=f"{self._url}/lol-login/v1/session")

        return session_response is not None and session_response.json()["error"] is not None

    def _get_player_uid(self) -> str | None:
        """
        Get the PUUID (globally unique ID) of the player.

        Returns:
            The PUUID as a string or None if there was an issue getting it.

        """
        session_response = _http_error_wrapper(self._session.get, url=f"{self._url}/lol-login/v1/session")

        return None if not session_response else session_response.json()["puuid"]

    def get_win_rate(self, number_of_games: int) -> str:
        """
        Get the win rate for the last N games.

        Args:
            number_of_games: The amount of the games to get the win rate for, min 1 max 20.

        Returns:
            A human-readable string holding the percentage, for example '20.3'.

        """
        player_uid = self._get_player_uid()
        # Clamp to min 1, max 20 games
        number_of_games = max(1, min(number_of_games, 20))

        matches_response = _http_error_wrapper(
            self._session.get,
            raise_and_catch=False,
            url=f"{self._url}/lol-match-history/v1/products/tft/{player_uid}/matches?count={number_of_games}",
        )

        try:
            matches_response.raise_for_status()
        except (AttributeError, HTTPError):
            return "ERROR"

        games = matches_response.json()["games"]
        games_played = len(games)
        wins = 0
        for game in games:
            player = [player for player in game["json"]["participants"] if player["puuid"] == player_uid][0]
            if player["placement"] <= 4:
                wins += 1

        return f"{(wins / games_played) * 100:.2f}"


class GameClientIntegration:
    """
    Class to integrate with the official Rito Game Client API.
    Sadly the TFT endpoint is re-using the normal League data format.
    At the moment the only useful data returned are the player health and the player level.
    """

    def __init__(self):
        self._url = "https://127.0.0.1:2999"
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        self._session.verify = "tft_bot/resources/riotgames_root_certificate.pem"

    def wait_for_game_window(
        self, lcu_integration: LCUIntegration, timeout: int, connection_error_counter: int = 0
    ) -> bool:
        """
        Waits for the API to be responsive, which also means the game window is available.

        Args:
            lcu_integration: The object to interact with the LCU.
            timeout: The approximate time to wait for a successful connection before giving up.
            connection_error_counter: The amount of times we received a connection error, should only be set by itself.

        Returns:
            True if we could connect to the API within a specified time, False if not

        """
        try:
            self._session.get(f"{self._url}", timeout=(timeout, None))
        except requests.exceptions.ConnectionError:
            if connection_error_counter == timeout:
                return False

            time.sleep(1)

            if lcu_integration.should_reconnect():
                lcu_integration.reconnect()
                time.sleep(5)

            return self.wait_for_game_window(
                lcu_integration=lcu_integration, timeout=timeout, connection_error_counter=connection_error_counter + 1
            )
        except requests.exceptions.Timeout:
            return False

        return True

    def game_loaded(self) -> bool:
        """
        Checks if the game has loaded.

        Returns:
            True if the game has loaded, False if not.

        """
        logger.debug("Checking if the game has loaded")

        event_data_response = _http_error_wrapper(self._session.get, url=f"{self._url}/liveclientdata/eventdata")
        return event_data_response is not None and len(event_data_response.json()["Events"]) > 0

    def is_dead(self) -> bool:
        """
        Checks if the user is considered dead, aka. has less than or equal to 0 HP.

        Returns:
            True if the user has less than or equal to 0 HP, else False

        """
        logger.debug("Checking if we have more than 0 HP")

        active_player_response = _http_error_wrapper(self._session.get, url=f"{self._url}/liveclientdata/activeplayer")
        if not active_player_response:
            logger.debug("There was an error in the response, assuming that we are dead")
            return True

        return active_player_response.json()["championStats"]["currentHealth"] <= 0.0

    def get_level(self) -> int:
        """
        Get the level the player currently is at.

        Returns:
            The level of the active player.
        """

        active_player_response = _http_error_wrapper(self._session.get, url=f"{self._url}/liveclientdata/activeplayer")
        if not active_player_response:
            logger.debug("There was an error in the response, assuming that we are level 0")
            return 0

        return active_player_response.json().get("level", 0)
