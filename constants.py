"""Common constants used throughout the codebase, and common groupings of them in array format."""

import os

CONSTANTS = {
    "storage": {"appdata": "%APPDATA%/TFT Bot"},
    "executables": {
        "league": {
            "client": r"\LeagueClient.exe",
            "client_ux": r"\LeagueClientUx.exe",
            "game": r"\Game\League of Legends.exe",
        },
    },
    "processes": {
        "client": "LeagueClient.exe",
        "client_ux": "LeagueClientUx.exe",
        "game": "League of Legends.exe",
    },
    "tft_logo": {
        "base": "captures/tft_logo.png",
        "overshadowed": "captures/tft_logo_overshadowed.png",
    },
    "client": {
        "screenshot_location": f"{os.getcwd()}/screenshots",
        "tabs": {
            "tft": {
                "unselected": {
                    "1": "captures/buttons/tab_tft_unselected_1.png",
                    "2": "captures/buttons/tab_tft_unselected_2.png",
                },
                "selected": "captures/buttons/tab_tft_selected.png",
                "subtab_home": "captures/buttons/tft_subtab_home.png"
            }
        },
        "pre_match": {
            "quick_play": "captures/buttons/quick_play.png",
            "find_match": {
                "base": "captures/buttons/find_match.png",
                "highlighted": "captures/buttons/find_match_highlighted.png",
            },
            "lobby": {
                "normal": "captures/tft_lobby_normal.png",
            },
        },
        "in_queue": {
            "base": "captures/buttons/in_queue.png",
            "overshadowed": "captures/buttons/in_queue_overshadowed.png",
            "accept": {
                "zoomed": "captures/buttons/accept_zoomed.png",
                "expanded": "captures/buttons/accept_expanded.png",
            }
        },
        "continue": "captures/buttons/continue.png",
        "death": "captures/death.png",
        "reconnect": "captures/buttons/reconnect.png",
        "key_fragment": {
            "one": "captures/buttons/key_fragment.png",
            "two": "captures/buttons/key_fragment2.png",
        },
        "post_game": {
            "skip_waiting_for_stats": {
                "original": "captures/buttons/skip_waiting_for_stats.png",
                "base": "captures/buttons/skip_waiting_for_stats_base.png",
                "highlighted": "captures/buttons/skip_waiting_for_stats_highlighted.png",
            },
            "play_again": "captures/buttons/play_again.png",
            "missions_ok": "captures/buttons/missions_ok.png",
        },
        "launcher_play": "captures/buttons/launcher_play.png",
        "messages": {
            "give_feedback": "captures/messages/give_feedback.png",
            "session_expired": "captures/messages/session_expired.png",
            "failed_to_reconnect": "captures/messages/failed_to_reconnect.png",
            "login_servers_down": "captures/messages/login_servers_down.png",
            "players_are_not_ready": "captures/messages/players_are_not_ready.png",
            "buttons": {
                "message_ok": "captures/buttons/message_ok.png",
                "message_exit": "captures/buttons/message_exit.png",
            },
        },
    },
    "game": {
        "loading": "captures/loading.png",
        "exit_now": {
            "base": "captures/buttons/exit_now_base.png",
            "highlighted": "captures/buttons/exit_now_highlighted.png",
            "original": "captures/buttons/exit_now_original.png",
        },
        "settings": "captures/buttons/settings.png",
        "surrender": {
            "surrender_1": "captures/buttons/surrender_1.png",
            "surrender_2": "captures/buttons/surrender_2.png",
        },
        "gamelogic": {
            "choose_one": "captures/buttons/choose_one.png",
            "reroll": "captures/buttons/reroll.png",
            "take_all": "captures/buttons/take_all.png",
            "timer_1": "captures/timer_1.png",
            "xp_buy": "captures/buttons/xp_buy.png",
        },
        "gold": {
            "0": "captures/gold/0.png",
            "1": "captures/gold/1.png",
            "2": "captures/gold/2.png",
            "3": "captures/gold/3.png",
            "4": "captures/gold/4.png",
            "5": "captures/gold/5.png",
            "6": "captures/gold/6.png",
        },
        "round": {
            "-4": "captures/round/-4.png",
            "1-": "captures/round/1-.png",
            "2-": "captures/round/2-.png",
            "3-": "captures/round/3-.png",
            "1-1": "captures/round/1-1.png",
            "2-2": "captures/round/2-2.png",
            "2-3": "captures/round/2-3.png",
            "2-4": "captures/round/2-4.png",
            "2-5": "captures/round/2-5.png",
            "3-1": "captures/round/3-1.png",
            "3-2": "captures/round/3-2.png",
            "3-3": "captures/round/3-3.png",
            "3-4": "captures/round/3-4.png",
            "3-7": "captures/round/3-7.png",
            "4-6": "captures/round/4-6.png",
            "4-7": "captures/round/4-7.png",
            "6-5": "captures/round/6-5.png",
            "6-6": "captures/round/6-6.png",
        },
        "trait": {
            "ace": "captures/trait/ace.png",
            "admin": "captures/trait/admin.png",
            "aegis": "captures/trait/aegis.png",
            "anima_squad": "captures/trait/anima_squad.png",
            "brawler": "captures/trait/brawler.png",
            "civilian": "captures/trait/civilian.png",
            "defender": "captures/trait/defender.png",
            "duelist": "captures/trait/duelist.png",
            "gadgeteen": "captures/trait/gadgeteen.png",
            "hacker": "captures/trait/hacker.png",
            "heart": "captures/trait/heart.png",
            "lasercorps": "captures/trait/lasercorps.png",
            "mascot": "captures/trait/mascot.png",
            "mecha_prime": "captures/trait/mecha_prime.png",
            "ox_force": "captures/trait/ox_force.png",
            "recon": "captures/trait/recon.png",
            "renegade": "captures/trait/renegade.png",
            "spellslinger": "captures/trait/spellslinger.png",
            "star_guardian": "captures/trait/star_guardian.png",
            "threat": "captures/trait/threat.png",
            "underground": "captures/trait/underground.png",
        },
    },
}

accept_match_images = [
    CONSTANTS["client"]["in_queue"]["accept"]["expanded"],
    CONSTANTS["client"]["in_queue"]["accept"]["zoomed"],
]

find_match_images = [
    CONSTANTS["client"]["pre_match"]["find_match"]["base"],
    CONSTANTS["client"]["pre_match"]["find_match"]["highlighted"],
]

exit_now_images = [
    CONSTANTS["game"]["exit_now"]["base"],
    CONSTANTS["game"]["exit_now"]["highlighted"],
    CONSTANTS["game"]["exit_now"]["original"],
]

skip_waiting_for_stats_images = [
    CONSTANTS["client"]["post_game"]["skip_waiting_for_stats"]["base"],
    CONSTANTS["client"]["post_game"]["skip_waiting_for_stats"]["highlighted"],
    CONSTANTS["client"]["post_game"]["skip_waiting_for_stats"]["original"],
]

key_fragment_images = [
    CONSTANTS["client"]["key_fragment"]["one"],
    CONSTANTS["client"]["key_fragment"]["two"],
]

wanted_traits = [
    CONSTANTS["game"]["trait"]["lasercorps"],
    CONSTANTS["game"]["trait"]["brawler"],
    CONSTANTS["game"]["trait"]["star_guardian"],
]

unselected_tft_tabs = [
    CONSTANTS["client"]["tabs"]["tft"]["unselected"]["1"],
    CONSTANTS["client"]["tabs"]["tft"]["unselected"]["2"],
]
