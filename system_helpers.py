import http.client as httplib
import logging
import os
import sys

import psutil
import win32com.client
import win32gui
import win32process

try:
    import ctypes
    import msvcrt
finally:
    pass

def set_active_window(window_id) -> None:
    # Try to account for every scenario
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    win32gui.BringWindowToTop(window_id)
    win32gui.SetForegroundWindow(window_id)
    win32gui.SetActiveWindow(window_id)


def bring_window_to_forefront(window_title, path_to_verify=None) -> None:
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


def find_in_processes(executable_path) -> bool:
    for proc in psutil.process_iter():
        try:
            if proc.exe() == executable_path:
                return True
        except Exception:
            # Nothing, we don't care
            continue
    return False


def have_internet(ip_to_ping="1.1.1.1") -> bool:
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


def disable_quickedit():
    # Disable QuickEdit mode on Windows terminal. QuickEdit pauses application
    # execution if the user selects/highlights/clicks within the terminal
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


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS # pylint: disable=no-member,protected-access
    except Exception:
        base_path = os.path.abspath(".")

    if relative_path.startswith(base_path):
        return relative_path
    return os.path.join(base_path, relative_path)
