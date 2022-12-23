"""Bot executable creation script."""
import PyInstaller.__main__

import constants

PyInstaller.__main__.run(
    [
        "tft.py",
        "--onefile",
        "--add-data",
        "captures;captures",
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
