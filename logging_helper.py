"""
Python dual-logging setup (console and log file),
supporting different log levels and colorized output

Created by Fonic <https://github.com/fonic>

Based on:
https://stackoverflow.com/a/13733863/1976617
https://uran198.github.io/en/python/2016/07/12/colorful-python-logging.html
https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
via https://gist.github.com/fonic/7e5ab76d951a2ab2d5f526a7db3e2004
"""

import ctypes
import logging
# Imports
import sys


class LogFormatter(logging.Formatter):
    """LogFormatter class which supports colorized output."""

    COLOR_CODES = {
        logging.CRITICAL: "\033[1;35m", # bright/bold magenta
        logging.ERROR:    "\033[1;31m", # bright/bold red
        logging.WARNING:  "\033[1;33m", # bright/bold yellow
        logging.INFO:     "\033[0;37m", # white / light gray
        logging.DEBUG:    "\033[1;30m"  # bright/bold black / dark gray
    }

    RESET_CODE = "\033[0m"

    def __init__(self, color, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color = color

    def format(self, record, *args, **kwargs):
        if (self.color is True and record.levelno in self.COLOR_CODES):
            record.color_on  = self.COLOR_CODES[record.levelno]
            record.color_off = self.RESET_CODE
        else:
            record.color_on  = ""
            record.color_off = ""
        return super().format(record, *args, **kwargs)

# Enable ANSI terminal mode for Command Prompt on Microsoft Windows
def try_windows_enable_ansi_terminal_mode() -> bool:
    """Try to enable Windows ANSI terminal mode.

    Returns:
        bool: True if success, False if not supported or failure.
    """
    if sys.platform != "win32":
        return False
    try:
        kernel32 = ctypes.windll.kernel32
        result = kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        if result == 0:
            raise Exception
        return True
    except Exception:
        return False

def setup_logging(console_log_output: str, console_log_level: str, console_log_color: bool, #pylint: disable=too-many-arguments
    logfile_file: str, logfile_log_level: str, logfile_log_color: bool, log_line_template: str) -> bool:
    """Setup logging.

    Args:
        console_log_output (str): The console output destination (stdout, stderr)
        console_log_level (str): The base log level that should log to console
        console_log_color (bool): Whether colour should be enabled in the console output (when available)
        logfile_file (str): The logfile target name
        logfile_log_level (str): The base log level that should log to logfile
        logfile_log_color (bool):  Whether colour should be enabled in the logfile output
        log_line_template (str): The log template/formatting to which the log should follow

    Returns:
        bool: True if successfully setup, False otherwise.
    """
    try_windows_enable_ansi_terminal_mode()
    # Create logger
    # For simplicity, we use the root logger, i.e. call 'logging.getLogger()'
    # without name argument. This way we can simply use module methods for
    # for logging throughout the script. An alternative would be exporting
    # the logger, i.e. 'global logger; logger = logging.getLogger("<name>")'
    logger = logging.getLogger()
    logger.handlers = []

    # Set global log level to 'debug' (required for handler levels to work)
    logger.setLevel(logging.DEBUG)

    # Create console handler
    console_log_output = console_log_output.lower()
    if console_log_output == "stdout":
        console_log_output = sys.stdout
    elif console_log_output == "stderr":
        console_log_output = sys.stderr
    else:
        print(f"Failed to set console output: invalid output: '{console_log_output}'")
        return False
    console_handler = logging.StreamHandler(console_log_output)

    # Set console log level
    try:
        console_handler.setLevel(console_log_level.upper()) # only accepts uppercase level names
    except Exception as exception:
        logging.critical(exception)
        print(f"Failed to set console log level: invalid level: '{console_log_level}'")
        return False

    # Create and set formatter, add console handler to logger
    console_formatter = LogFormatter(fmt=log_line_template, color=console_log_color)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create log file handler
    try:
        logfile_handler = logging.FileHandler(logfile_file)
    except Exception as exception:
        print(f"Failed to set up log file: {str(exception)}")
        return False

    # Set log file log level
    try:
        logfile_handler.setLevel(logfile_log_level.upper()) # only accepts uppercase level names
    except Exception as exception:
        logging.critical(exception)
        print(f"Failed to set log file log level: invalid level: '{logfile_log_level}'")
        return False

    # Create and set formatter, add log file handler to logger
    logfile_formatter = LogFormatter(fmt=log_line_template, color=logfile_log_color)
    logfile_handler.setFormatter(logfile_formatter)
    logger.addHandler(logfile_handler)

    # Success
    return True
