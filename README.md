# Python TFT Auto Battler Bot
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

This is an auto TFT bot, with some decent logic built in.

> ⚠️ WARNING
> Users have been reporting an uptick in bans while utilizing TFT botting software. Users of this repo appear to have all been related to using the executable releases, and as such we are removing the uploaded executables from future releases. It is strongly advised against building them yourselves or using older releases, at this time.
> We can not currently verify if there are source-code users being banned as well, and until we hear otherwise, would recommend users stick to running the python/source method only.
> Checkpoints / times that users should update their local git copy will be noted with 'releases' in the same consistentcy as before, just without the executables to be downloaded.

Some features of this bot:
- Compiles to release executables, so you do not need Python / pip installed in order to use it.
  - This includes being able to completely customize how the bot works through a [config file](#configuration), so you do not need to install python / pip for this either.
- Keyboard shortcuts use the [keyboard](https://pypi.org/project/keyboard/) package, which allows it to listen globally (so you don't need to have the console selected in the foreground for this to take effect)
  - Ability to pause/resume the bot using `alt+p`
  - Ability to not re-queue the bot for a new game using `alt+n`
- Does not surrender games early, by default, allowing it to play out most games, which at the ELO your bot will end up at means there's a decent chance you end up in top 4
  - If you're using this for event pass grinding, it will increase your odds of being top 4 which increases the points earned per minute played (faster pass progression)
- Draft stage pathing (does not just walk to one point, will walk counter-clockwise to try to ensure it picks up a champ)
- Two gold-based decision-making systems, a default one (requires **no** dependency) and a higher-effort one (requires additional dependency).
- Automatically detects your League install location from the Windows registry.
  - This means the bot is able to freely start and restart your league client, should any issues arise, no matter where you installed it.

How stable is this you might ask?
I recorded this screenshot after a couple days if it running straight, and the battlepass XP matches 😜

![image](https://user-images.githubusercontent.com/7606153/208268290-8956bfb0-62d4-4d2f-9dd9-0c17c4c1a20e.png)

# Usage / Settings

* Adding the (`-f` or `--ffearly`) argument will make it forfeit at the first opportunity
* Adding the (`-v` or `--verbose`) argument will enable more verbose debug logging
  * This toggles whether the verbose logging should log to console / window. Verbose logging will always log to the log file.
* You can use the config file below to "save" these settings

## Optional: Install Tesseract-OCR & Enable economic decision-making

By default, or if we could not find tesseract on your system, the bot will use a straight-forward logic of constantly leveling, rolling and buying units.
To change this, we support economic decision-making backed by reading the accurate value of your gold from your screen.
However, this **requires** Tesseract-OCR to be installed, which you can download a pre-built Windows installer for [here](https://github.com/UB-Mannheim/tesseract/wiki).
For this bots purpose, you can deselect everything in the components to install to only install the bare minimum.

After you have downloaded and installed Tesseract-OCR, set `mode` under `economy` to `ocr_standard` in the `config.yaml`.

The bot will (at its next start-up) attempt to detect where Tesseract is installed.

If that does not work, please manually override it in the `config.yaml`.

## Configuration
If you want to use frequent settings / "set it and forget it", you can do so by editing the `config.yaml` file in the data folder (exe: `%APPDATA%\TFT Bot`, python/source: `.\output\`).
If you don't see the file or folder, start the bot once, and it should be created.  
You can set the following settings:

* Level of information displayed to you
* Forfeiting early
* Overriding the assumed League Of Legends installation path
* Traits the bot should look for and how they should be bought
* Timeouts the bot waits for throughout its various loop logic parts

The settings are explained in more detail in the [file itself](tft_bot/resources/config.yaml).

The priority for configuration is as follows:

1. CLI Arguments - Anything passed directly in the command-line takes the highest priority
2. Configuration - Anything set in the configuration file
3. Fallback default - Default values the developers deemed sensible

# Installation (for source):

* Install Python 3.11 from [here](https://www.python.org/downloads/), or the Windows Store
* Navigate to your install directory using `cd` and set up your virtual environment using:
```bash
python3 -m pip install --user virtualenv
python3 -m venv envw
```
* Activate the virtual environment any time you wish to run the bot by using `.\envw\Scripts\activate` in your terminal, which should then show `(envw)` to the left of the line (`(envw) C:\tft-bot` for example)
* In the virtual environment, install the package dependencies by running `pip install -r requirements.txt` in Command Prompt
* In the virtual environment, start the bot by running `python tft.py` in Command Prompt
* Follow the instructions in your terminal window! Get into a TFT lobby, have the created window visible on your screen, and press 'OK' to start the bot!

***Note**: The data folder is `./output` when running the python script directly.*

# Troubleshooting:

Common Issues:
* The bot is configured to work with in-game resolution 1920x1080, and League client resolution 1280x720. (Also Windows scaling 100%) You can switch this up though, just re-capture the images in the captures folder, but support will become more difficult!
* Make sure you have any overlays over the normal League game window disabled.

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
