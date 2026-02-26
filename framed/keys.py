import curses
import os


CR = 13  # Carriage Return
LF = 10  # Line Feed

if os.uname().sysname == "Darwin":
    # MacOS likes to be different, I guess
    BACKSPACE = 127
    DELETE = 330
else:
    BACKSPACE = 8
    DELETE = 127

LEFT = curses.KEY_LEFT
RIGHT = curses.KEY_RIGHT
UP = curses.KEY_UP
DOWN = curses.KEY_DOWN

ENTER = 10
RETURN = 13
