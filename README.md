# Python TFT Auto Battler Bot
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

This is an auto TFT bot, with some decent logic built in.

Some features of this bot:
- Keyboard shortcuts use the [keyboard](https://pypi.org/project/keyboard/) package, which allows it to listen globally (so you don't need to have the console selected in the foreground for this to take effect)
  - Ability to pause/resume the bot using `alt+p`
  - Ability to not re-queue the bot for a new game using `alt+n`
- Does not surrender games early, by default, allowing it to play out most games, which at the ELO your bot will end up at means there's a decent chance you end up in top 4
  - If you're using this for event pass grinding, it will increase your odds of being top 4 which increases the points earned per minute played (faster pass progression)
- Draft stage pathing (does not just walk to one point, will walk counter-clockwise to try to ensure it picks up a champ)
- Basic gold logic to only click based on the gold available
  - If >= 4, buy xp
  - If >= 1, attempt 3 champ purchases
    - After that, if >= 2, re-roll
- Compiles to release executables so you do not need Python / pip installed in order to use it
- Can load settings from a config file (if you want to customize how it starts up)
- Automatically detects your League install location from the Windows registry, allowing non-default installs to still benefit from this script

How stable is this you might ask?
I recorded this screenshot after a couple days if it running straight, and the battlepass XP matches 😜

![image](https://user-images.githubusercontent.com/7606153/208268290-8956bfb0-62d4-4d2f-9dd9-0c17c4c1a20e.png)



# Usage / Settings

* Adding the (`-f` or `--ffearly`) argument will make it forfeit at the first opportunity
* Adding the (`-v` or `--verbose`) argument will enable more verbose debug logging
  * This toggles whether the verbose logging should log to console / window. Verbose logging will always log to the log file.
* You can use the config file below to "save" these settings

## Configuration
If you want to use frequent settings / "set it and forget it", you can do so by editing the `config.yaml` file in the data folder (`%APPDATA%\TFT Bot`).
If you don't see the file or folder, start the bot once, and it should be created.  
You can set the following settings:

* Verbosity
* Forfeiting early
* Overriding the assumed League Of Legends installation path
* Traits the bot should look for and how they should be bought

The settings are explained below but also in more detail in the file itself.

The priority for configuration is as follows:

1. CLI Arguments - Anything passed directly in the command-line takes the highest priority
2. Configuration - Anything set in the configuration file
3. Fallback default - Default values the developers deemed sensible

***Note for developers**: The data folder is `./output` when running the python script directly.*

### *Advanced Setting Info*
#### **Verbose**
Enable verbose logging to the console window.
#### **Forfeit Early**
Forfeit at first opportunity instead of playing it out until eliminated.
#### **Override Install Location**
Override any League client detection logic. This should be set to whichever directory contains your `LeagueClient.exe`, `LeagueClientUx.exe`, and `Game\League of Legends.exe` executables, which is especially useful for Garena players as I can not automate this detection (from what I've heard).
#### **Wanted Traits**
Which traits the bot should look for.
#### **Purchase traits in prioritized order**
If a trait in the configured trait list should only be bought if the trait that comes before it was bought. 

# Installation (for source):

* Install Python 3.11 from [here](https://www.python.org/downloads/), or the Windows Store
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


If your issue isn't listed here, please create an [issue](https://github.com/Kyrluckechuck/tft-bot/issues), including the log file located at  
`%APPDATA%\TFT Bot\tft-bot-debug-TIMESTAMP.log` (running from release/executable) or  
`output\tft-bot-debug-TIMESTAMP.log` (running from Python),  
and any relevant screenshots or information that may help speed up resolving your issue.

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


# Contributing

Please follow the steps in [Installation (for source)](#installation-for-source) first.

After you have installed the project locally and have made (and tested) your changes,
please make sure that your changes are formatted correctly.

To do so, you can either permanently install a hook that runs before all of your commits
with `pre-commit install`, or run it once with `pre-commit run --all-files`.

When opening a PR, please describe your changes and why you made them.
