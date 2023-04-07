"""Bot executable creation script."""
import PyInstaller.__main__

from tft_bot import constants

PyInstaller.__main__.run(
    [
        "tft.py",
        "--onefile",
        "--add-data",
        "captures;captures",
        "--add-data",
        "tft_bot/resources;tft_bot/resources",
        "-n",
        "TFT Bot",
        "-i",
        "tft_logo_with_bot.ico",
        "--console",
        "--win-private-assemblies",
        "--win-no-prefer-redirects",
        "--clean",
        "--runtime-tmpdir",
        constants.CONSTANTS["storage"]["appdata"],
    ]
)
