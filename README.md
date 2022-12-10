# Python TFT Auto Battler Bot
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

This is an auto TFT bot, with some decent logic built in.

Some features of this bot:
- Ability to pause/resume the bot using `alt+p`
  - This uses the [keyboard](https://pypi.org/project/keyboard/) package, which allows it to listen globally (so you don't need to have the console selected in the foreground for this to take effect)
- Does not surrender, allowing it to play out most games, which at the ELO your bot will end up at means there's a decent chance you end up in top 4
  - If you're using this for event pass grinding, it will increase your odds of being top 4 which increases the points earned per minute played
- Draft stage pathing (does not just walk to one point, will walk counter-clockwise to try to ensure it picks up a champ)
- Basic gold logic to only click based on the gold available
  - If >= 4, buy xp 
  - If >= 1, attempt 3 champ purchases
    - After that, if >= 2, re-roll
- Compiles to release executables so you do not need Python / pip installed in order to use it
- Can load settings from a config file (if you want to customize how it starts up)
- Automatically detects your League install location from the Windows registry, allowing non-default installs to still benefit from this script


# Usage / Settings

* Adding the `--ffearly` argument will make it forfeit at the first opportunity
* Adding the (`-v` or `--verbose`) argument will enable more verbose debug logging
  * This toggles whether the verbose logging should log to console / window. Verbose logging will always log to the log file.
* You can use the config file below to "save" these settings

## Config Structure
If you want to use frequent settings / "set it and forget it", you can do so by creating `bot-settings.ini` in the same directory as the python script or release executable with the following structure:
```ini
[SETTINGS]
Verbose = True
ForfeitEarly = False
```

Any setting not specified will fall back on the default behaviour, though CLI settings will take highest precedence (overriding config settings).

# Installation (for source):

* Install Python 3.10 from [here](https://www.python.org/downloads/), or the Windows Store
* Navigate to your install directory using `cd` and run `pip install -r requirements.txt` in Command Prompt
* Navigate to your install directory using `cd` and run `py tft.py` in Command Prompt
* Follow the instructions in your terminal window! Get into a TFT lobby, have the created window visible on your screen, and press 'OK' to start the bot!

# Troubleshooting:

Common Issues:
* The bot is configured to work with in-game resolution 1920x1080, and League client resolution 1280x720. (Also Windows scaling 100%) You can switch this up though, just re-capture the images in the captures folder, but support will become more difficult!
* Make sure to run League and the bot on your main monitor, as it doesn't support additional monitors!

If running from source:
* If these steps don't work, try running the file with `python "tft.py"` instead (For Windows Store/MacOS/Linux users especially) Likewise, try `pip3` instead of `pip` for installing requirements.
* If pip doesn't seem to exist, try installing it [here](https://pip.pypa.io/en/stable/installing/). Essentially 'save as' from [here](https://bootstrap.pypa.io/get-pip.py), then run `py get-pip.py` and try to use pip again
* If you're having issues with Python not working properly, please make sure you have the correct version installed, and have done a `pip install -r requirements.txt` prior to running.


If your issue isn't listed here, please create an [issue](https://github.com/Kyrluckechuck/tft-bot/issues), including the log file located at `%APPDATA%/TFT Bot/TFT Bot.log` (running from release/executable) or `%APPDATA%/TFT Bot/tft.log` (running from Python), and any relevant screenshots or information that may help speed up resolving your issue.

## Info / Why I forked it
I've fairly heavily forked this from what it originally was, but if you'd like to see the original, I'm not claiming to have made this from scratch:

- https://github.com/Detergent13

I decided to fork this after being frustrated with the lack of updates and/or features, and the delay it would take in getting PRs merged even if the work is done by the community. I had been using this modified script for a while now, but realized I may as well formally fork & upload it since it's been fairly stable.

To be clear I don't blame Detergent13 at all, I just have different feelings about what belongs in the bot / envisions for what this could become.

For example:
- I've completely removed the event-bubble style that the code was previously written to utilize, and instead uses an event-loop style system (which is much cleaner and less prone to breaking IMO)
  - One major benefit of this change, is that the bot can now start mid-game and will resume when it finds the first recognizable marker
- Update some of the logic to be based on the executable running, since there's no point attempting them if the game isn't open
- Introduce "constants" style paths, allowing cleaner re-use of image/file locations
- Added gold logic from [this pr](https://github.com/Detergent13/tft-bot/pull/91) which was stale/stuck

On that note, if anyone has any suggestions / features they would like to see, please feel free to suggest in an [issue](https://github.com/Kyrluckechuck/tft-bot/issues), or by submitting your own PR to this!