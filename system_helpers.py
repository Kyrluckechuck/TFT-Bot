"""A collection of system-level helpers"""
import http.client as httplib
import logging
import os
import pathlib
import sys
import winreg

import psutil
import win32com.client
import win32gui
import win32process

try:
    import ctypes
    import msvcrt
except Exception:
    pass

def set_active_window(window_id: int) -> None:
    """Sets the currently active window and focus.

    Args:
        window_id (int): The window ID to use
    """
    # Try to account for every scenario
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    win32gui.BringWindowToTop(window_id)
    win32gui.SetForegroundWindow(window_id)
    win32gui.SetActiveWindow(window_id)


def bring_window_to_forefront(window_title: str, path_to_verify: str | None=None) -> None:
    """Bring the first window found matching the requested title to the forefront and focus/make active.

    Args:
        window_title (str): The window title to match/look for.
        path_to_verify (str | None, optional): If provided, validates the window found matching the title is this executable path. Defaults to None.
    """
    try:
        hwnd = win32gui.FindWindowEx(0, 0, 0, window_title)
        if path_to_verify is not None:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            path = psutil.Process(pid).exe()
            if path != path_to_verify:
                logging.debug(f"Failed to find process to bring to forefront:\n\t{path} != {path_to_verify}")
                return
        set_active_window(hwnd)
    except Exception as err:
        logging.debug(f"Failed to click to {err}")


def find_in_processes(executable_path: str) -> bool:
    """Find if the provided executable path is one of the currently active processes.

    Args:
        executable_path (str): The executable path to check for.

    Returns:
        bool: True if the requested executable path was found, False otherwise.
    """
    for proc in psutil.process_iter():
        try:
            if proc.exe() == executable_path:
                return True
        except Exception:
            # Nothing, we don't care
            continue
    return False


def have_internet(ip_to_ping="1.1.1.1") -> bool:
    """Checks if there is an active internet connection to the given IP address, checking if a HEAD request succeeds.

    Args:
        ip_to_ping (str, optional): The IP address to check. Defaults to "1.1.1.1".

    Returns:
        bool: True if a HEAD request succeeds to the specified IP address, False otherwise.
    """
    conn = httplib.HTTPSConnection(ip_to_ping, timeout=5)
    try:
        conn.request("HEAD", "/")
        logging.debug(F"Success pinging {ip_to_ping}")
        return True
    except Exception:
        logging.debug(F"Can not ping {ip_to_ping}")
        return False
    finally:
        conn.close()

# Via https://gist.github.com/sthonnard/31106e47eab8d6f3329ef530717e8079
def disable_quickedit() -> None:
    """Disable QuickEdit mode on Windows terminal. QuickEdit pauses application execution if the user selects/highlights/clicks within the terminal."""
    if not os.name == 'posix':
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            device = r'\\.\CONIN$'
            with open(device, 'r') as con: # pylint: disable=unspecified-encoding
                file_handle = msvcrt.get_osfhandle(con.fileno())
                kernel32.SetConsoleMode(file_handle, 0x0080)
        except Exception as err:
            logging.warning(f'Cannot disable QuickEdit mode! : {str(err)}')
            logging.warning('As a consequence, execution might be automatically paused, careful where you click!')


def resource_path(relative_path: str) -> str:
    """Convert the given relative path to the expanded temp directory path.

    Args:
        relative_path (str): The relative path to expand.

    Returns:
        str: The relative path prefixed with the runtime directory.
    """
    try:
        base_path = sys._MEIPASS # pylint: disable=no-member,protected-access
    except Exception:
        base_path = os.path.abspath(".")

    if relative_path.startswith(base_path):
        return relative_path
    return os.path.join(base_path, relative_path)

def expand_environment_variables(var: str) -> str:
    """Expands the provided variable for any included environment variables.

    Args:
        var (str): The string containing environment variables.

    Returns:
        str: The string with any environment variables replaced.
    """
    return os.path.expandvars(var)

def determine_league_install_location(override_path: str | None=None) -> str:
    """Determine the location League was installed.

    Args:
        override_path (str): A path to override any client detection logic.

    Returns:
        str: If successful, the determined install location. If unsuccessful, the default install location.
    """
    # Assign default just in case it failed to be found
    league_path = r"C:\Riot Games\League of Legends"

    if override_path is not None:
        logging.warning(f'Override path supplied, using \'{override_path}\' as League install directory.')
        league_path = override_path
    else:
        try:
            access_registry = winreg.ConnectRegistry(None,winreg.HKEY_CURRENT_USER)
            access_key = winreg.OpenKey(
                access_registry, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Riot Game league_of_legends.live', 0, winreg.KEY_READ
            )
            [league_path, _] = winreg.QueryValueEx(access_key, "InstallLocation")
        except Exception as err:
            logging.error(f'Could not dynamically determine League install location : {str(err)}')
            logging.error(sys.exc_info())

    league_path = str(pathlib.PureWindowsPath(league_path))

    logging.debug(f"League path determined to be: {league_path}")

    return league_path
