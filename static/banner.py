import os

def get_terminal_width():
    """Returns the width of the terminal."""
    try:
        _, columns = os.get_terminal_size()
        return int(columns)
    except OSError:
        # Default terminal width if the size cannot be determined
        return 80

def display_banner():
    """Displays a banner, centered in the terminal."""
    banner = [
        "",
        "  _____           _      _____              _                 _     ",
        " |  ___|   _  ___| | __ |  ___|_ _  ___ ___| |__   ___   ___ | | __ ",
        " | |_ | | | |/ __| |/ / | |_ / _` |/ __/ _ \ '_ \ / _ \ / _ \| |/ / ",
        " |  _|| |_| | (__|   <  |  _| (_| | (_|  __/ |_) | (_) | (_) |   <  ",
        " |_|   \__,_|\___|_|\_\ |_|  \__,_|\___\___|_.__/ \___/ \___/|_|\_\ ",
        "",
        "                          ┌──────────────┐                          ",
        "                          │ By Ph4nToM00 │                          ",
        "                          └──────────────┘                          ",
        "                    Paypal: paypal.me/UnderRadio                    ",
        "               Github: https://github.com/Ph4nToM00                 ",
    ]

    terminal_width = get_terminal_width()
    centered_banner = [line.center(terminal_width) for line in banner]
    
    return centered_banner
