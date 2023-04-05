"""
Integrations with the Rito API to have the most reliable data where possible.
"""
import time

from loguru import logger
from psutil import Process
from psutil import process_iter
import requests
from requests import HTTPError

# Potentially make this configurable in the future
# to let the user select their preferred tft mode.
TFT_NORMAL_GAME_QUEUE_ID = 1090
ROOT_CERTIFICATE = """-----BEGIN CERTIFICATE-----
MIIEIDCCAwgCCQDJC+QAdVx4UDANBgkqhkiG9w0BAQUFADCB0TELMAkGA1UEBhMC
VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFTATBgNVBAcTDFNhbnRhIE1vbmljYTET
MBEGA1UEChMKUmlvdCBHYW1lczEdMBsGA1UECxMUTG9MIEdhbWUgRW5naW5lZXJp
bmcxMzAxBgNVBAMTKkxvTCBHYW1lIEVuZ2luZWVyaW5nIENlcnRpZmljYXRlIEF1
dGhvcml0eTEtMCsGCSqGSIb3DQEJARYeZ2FtZXRlY2hub2xvZ2llc0ByaW90Z2Ft
ZXMuY29tMB4XDTEzMTIwNDAwNDgzOVoXDTQzMTEyNzAwNDgzOVowgdExCzAJBgNV
BAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlhMRUwEwYDVQQHEwxTYW50YSBNb25p
Y2ExEzARBgNVBAoTClJpb3QgR2FtZXMxHTAbBgNVBAsTFExvTCBHYW1lIEVuZ2lu
ZWVyaW5nMTMwMQYDVQQDEypMb0wgR2FtZSBFbmdpbmVlcmluZyBDZXJ0aWZpY2F0
ZSBBdXRob3JpdHkxLTArBgkqhkiG9w0BCQEWHmdhbWV0ZWNobm9sb2dpZXNAcmlv
dGdhbWVzLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKoJemF/
6PNG3GRJGbjzImTdOo1OJRDI7noRwJgDqkaJFkwv0X8aPUGbZSUzUO23cQcCgpYj
21ygzKu5dtCN2EcQVVpNtyPuM2V4eEGr1woodzALtufL3Nlyh6g5jKKuDIfeUBHv
JNyQf2h3Uha16lnrXmz9o9wsX/jf+jUAljBJqsMeACOpXfuZy+YKUCxSPOZaYTLC
y+0GQfiT431pJHBQlrXAUwzOmaJPQ7M6mLfsnpHibSkxUfMfHROaYCZ/sbWKl3lr
ZA9DbwaKKfS1Iw0ucAeDudyuqb4JntGU/W0aboKA0c3YB02mxAM4oDnqseuKV/CX
8SQAiaXnYotuNXMCAwEAATANBgkqhkiG9w0BAQUFAAOCAQEAf3KPmddqEqqC8iLs
lcd0euC4F5+USp9YsrZ3WuOzHqVxTtX3hR1scdlDXNvrsebQZUqwGdZGMS16ln3k
WObw7BbhU89tDNCN7Lt/IjT4MGRYRE+TmRc5EeIXxHkQ78bQqbmAI3GsW+7kJsoO
q3DdeE+M+BUJrhWorsAQCgUyZO166SAtKXKLIcxa+ddC49NvMQPJyzm3V+2b1roP
SvD2WV8gRYUnGmy/N0+u6ANq5EsbhZ548zZc+BI4upsWChTLyxt2RxR7+uGlS1+5
EcGfKZ+g024k/J32XP4hdho7WYAS2xMiV83CfLR/MNi8oSMaVQTdKD8cpgiWJk3L
XWehWA==
-----END CERTIFICATE-----
"""
ROOT_CERTIFICATE_PATH = ""


def write_root_certificate_to_file(path: str) -> None:
    """
    Writes the Riot root certificate to a file in the file system, because requests needs it to be a file.
    We need the certificate for SSL connections to any of Riot's APIs.
    """
    with open(file=f"{path}\\riotgames_root_certificate.pem", mode="w", encoding="UTF-8") as file:
        file.write(ROOT_CERTIFICATE)
    global ROOT_CERTIFICATE_PATH
    ROOT_CERTIFICATE_PATH = path


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


class LCUIntegration:
    """
    Integrates the bot with League Client Update (LCU) API.
    Note that the API is allowed to use, but not officially supported by Rito.
    The endpoints we use are stable-ish, and we do not expect them to change soonTM.
    """

    def __init__(self):
        self._session = None
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
        logger.info("Waiting for the League client (~5m timeout)")
        lcu_process = get_lcu_process()

        timeout = 0
        while not lcu_process:
            if timeout >= 300:
                logger.warning("Couldn't find the League client within 5 minutes, exiting")
                return False
            logger.debug("Couldn't find LCUx process yet. Re-searching process list...")
            time.sleep(1)
            lcu_process = get_lcu_process()
            timeout += 1

        logger.debug("LCUx process found")
        process_arguments = _get_lcu_commandline_arguments(lcu_process)
        self.install_directory = process_arguments["install-directory"]
        self._url = f"https://127.0.0.1:{process_arguments['app-port']}"
        _auth_key = process_arguments["remoting-auth-token"]

        if self._session is not None:
            logger.debug("LCU session already existed, closing it just to be safe.")
            self._session.close()

        self._session = requests.Session()
        self._session.auth = ("riot", _auth_key)
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        self._session.verify = f"{ROOT_CERTIFICATE_PATH}\\riotgames_root_certificate.pem"

        logger.info("League client found, trying to connect to it (~60s timeout)")
        timeout = 0
        while True:
            if timeout >= 60:
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
            logger.info("Waiting for client availability (~120s timeout)")
            timeout = 0
            while timeout < 120:
                availability_response = self._session.get(url=f"{self._url}/lol-gameflow/v1/availability")
                if availability_response.status_code == 200 and availability_response.json()["isAvailable"]:
                    logger.info("Client available, queue logic should start")
                    return True
                time.sleep(1)
                timeout += 1
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
        get_lobby_response = self._session.get(
            f"{self._url}/lol-lobby/v2/lobby",
        )

        try:
            get_lobby_response.raise_for_status()
        except HTTPError:
            return False

        return get_lobby_response.json()["gameConfig"]["queueId"] == TFT_NORMAL_GAME_QUEUE_ID

    def create_lobby(self) -> bool:
        """
        Create a lobby of the type we want.

        Returns:
            True if we succeeded in creating it, False if not.

        """
        logger.info("Creating a TFT lobby")
        create_lobby_response = self._session.post(
            f"{self._url}/lol-lobby/v2/lobby", json={"queueId": TFT_NORMAL_GAME_QUEUE_ID}
        )

        return create_lobby_response.status_code == 200

    def delete_lobby(self) -> None:
        """
        Forcefully closes the current lobby, useful for "Player is not ready" bugs etc.
        """
        logger.info("Closing the lobby because it seems we got stuck")
        self._session.delete(
            f"{self._url}/lol-lobby/v2/lobby",
        )

    def start_queue(self) -> bool:
        """
        Start finding a match.

        Returns:
            True if we succeeded in starting the search, False if not.

        """
        logger.info("Starting the match finding queue")
        start_queue_response = self._session.post(
            f"{self._url}/lol-lobby/v2/lobby/matchmaking/search",
        )
        return start_queue_response.status_code == 204

    def in_queue(self) -> bool:
        """
        Checks if we are in a match finding queue.

        Returns:
            True if we are in a match finding queue, False if not.

        """
        logger.debug("Checking if we are already in a queue")
        get_queue_response = self._session.get(
            f"{self._url}/lol-lobby/v2/lobby/matchmaking/search-state",
        )

        if get_queue_response.status_code != 200:
            return False

        return get_queue_response.json()["searchState"] in {"Searching", "Found"}

    def found_queue(self) -> bool:
        """
        Checks if we have found a match that we need to accept.

        Returns:
            True if we have found a match that we need to accept, False if not.

        """
        logger.debug("Checking if we have found a match")
        get_queue_response = self._session.get(
            f"{self._url}/lol-lobby/v2/lobby/matchmaking/search-state",
        )

        if get_queue_response.status_code != 200:
            return False

        return get_queue_response.json()["searchState"] == "Found"

    def queue_accepted(self) -> bool:
        """
        Checks if we have accepted the match.

        Returns:
            True if we have accepted the match, False if not.

        """
        logger.debug("Checking if we already accepted the queue")
        ready_check_state = self._session.get(f"{self._url}/lol-matchmaking/v1/ready-check")

        if ready_check_state.status_code != 200:
            return False

        return ready_check_state.json()["playerResponse"] == "Accepted"

    def accept_queue(self) -> None:
        """
        Accept the match.
        """
        logger.info("Match ready, accepting the queue")
        self._session.post(f"{self._url}/lol-matchmaking/v1/ready-check/accept")

    def in_game(self) -> bool:
        """
        Checks if we are in a game.

        Returns:
            True if we are in a game, False if not.

        """
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

        return session_response.json()["phase"] in {"ChampSelect", "GameStart", "InProgress", "Reconnect"}

    def should_reconnect(self) -> bool:
        """
        Checks if we should reconnect to an existing game.

        Returns:
            True if we need to reconnect, False if not.

        """
        logger.debug("Checking if we should reconnect")
        session_response = self._session.get(
            f"{self._url}/lol-gameflow/v1/session",
        )

        if session_response.status_code != 200:
            return False

        return session_response.json()["phase"] == "Reconnect"


class GameClientIntegration:
    """
    Class to integrate with the official Rito Game Client API.
    Sadly the TFT endpoint is re-using the normal League data format.
    At the moment the only useful data returned are the player health and the player level.
    """

    def __init__(self):
        self._url = "https://127.0.0.1:2999"
        self._session = None

    def create_live_game_client_session(self) -> None:
        """
        Creates and caches a session that sets default headers and holds the Rito root SSL certificate.
        """
        logger.debug("Creating a session object that holds the root SSL certificate")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        self._session.verify = f"{ROOT_CERTIFICATE_PATH}\\riotgames_root_certificate.pem"

    def is_dead(self) -> bool:
        """
        Checks if the user is considered dead, aka. has less than or equal to 0 HP.

        Returns:
            True if the user has less than or equal to 0 HP, else False

        """
        logger.debug("Checking if we have more than 0 HP")
        if not self._session:
            self.create_live_game_client_session()

        active_player_response = self._session.get(f"{self._url}/liveclientdata/activeplayer")
        try:
            active_player_response.raise_for_status()
        except HTTPError:
            logger.debug("There was an error in the response, assuming that we are dead")
            return True

        active_player_data = active_player_response.json()
        return active_player_data["championStats"]["currentHealth"] <= 0.0
