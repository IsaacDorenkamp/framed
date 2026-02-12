import curses
import random


def setup():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_GREEN)


def get_random_color_attr():
    return curses.color_pair(random.choice((1, 2, 3)))
