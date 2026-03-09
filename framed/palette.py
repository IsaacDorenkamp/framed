import curses
import typing


class ColorError(Exception):
    pass


ColorInfo = tuple[str, int]

default_color = "default"
default_color_info = ("default", -1)


__can_change: bool = False
__colors: dict[str, int] = {}
__aliases: dict[str, str] = {}
__color_id: int = 0
__pairs:  dict[tuple[int, int], int] = {}
__pair_id: int = 1


def setup():
    curses.start_color()
    curses.use_default_colors()
    global __can_change
    global __colors
    global __color_id
    __can_change = curses.can_change_color()
    __colors = {
        default_color: -1,
        "black": curses.COLOR_BLACK,
        "blue": curses.COLOR_BLUE,
        "cyan": curses.COLOR_CYAN,
        "green": curses.COLOR_GREEN,
        "magenta": curses.COLOR_MAGENTA,
        "red": curses.COLOR_RED,
        "white": curses.COLOR_WHITE,
        "yellow": curses.COLOR_YELLOW,
    }
    __color_id = max(__colors.values()) + 1
    __pairs.clear()


def create_color(name: str, r: int, g: int, b: int):
    if not __can_change:
        raise ColorError("Terminal does not permit color changes.")

    global __color_id
    if __color_id >= curses.COLORS:
        raise ColorError("Could not create color (terminal allows %d)")

    if name in __colors:
        raise ColorError("Color '%s' already exists" % name)

    try:
        curses.init_color(__color_id, r, g, b)
    except curses.error as err:
        raise ColorError("Failed to create color (%d, %d, %d)" % (r, g, b)) from err

    __colors[name] = __color_id
    __color_id += 1


def set_color(name: str, r: int, g: int, b: int):
    if not __can_change:
        raise ColorError("Terminal does not permit color changes.")

    if name not in __colors:
        raise ColorError(f"No such color: {name}")

    color_id = __colors[name]
    try:
        curses.init_color(color_id, r, g, b)
    except curses.error as err:
        raise ColorError("Failed to set color (%d, %d, %d)" % (r, g, b)) from err


def alias(color: str, alias: str):
    if alias in __colors:
        raise ValueError(f"'{alias}' is already a named color!")

    if color not in __colors:
        raise ValueError(f"'{color}' is not a named color!")

    __aliases[alias] = color


def is_alias(color: str):
    return color in __aliases


def __aliased(name: str) -> str:
    if name in __aliases:
        return __aliases[name]

    return name


def color_pair(foreground: str, background: str) -> int:
    pair = __colors[__aliased(foreground)], __colors[__aliased(background)]
    if pair not in __pairs:
        global __pair_id
        curses.init_pair(__pair_id, *pair)
        __pairs[pair] = __pair_id
        __pair_id += 1
    return curses.color_pair(__pairs[pair])


def validate(color: str) -> tuple[str, int]:
    try:
        return color, __colors[__aliased(color)]
    except KeyError:
        raise ColorError(f"No such color: {color}")


def get_color_names() -> typing.Generator[str, None, None]:
    yield from __colors.keys()


__all__ = [
    "ColorError",
    "ColorInfo",
    "default_color",
    "default_color_info",
    "setup",
    "create_color",
    "set_color",
    "color_pair",
    "get_color_names",
]
