import curses
import typing

from .manager import Manager, StackManager, MultiplexManager, Direction
from .panel import Panel
from .struct import rect2, vec2
from . import _log


PanelType = typing.TypeVar("PanelType", bound=Panel)


class AppError(Exception):
    pass


class App:
    __stdscr: curses.window
    __size: vec2

    __running: bool
    __manager: Manager | None
    __control_handler: typing.Callable[[int], typing.Any] | None

    def __init__(self, stdscr: curses.window):
        self.__stdscr = stdscr
        self.__size = vec2(*stdscr.getmaxyx())
        self.__running = True
        self.__manager = None
        self.__control_handler = None

    # --- Layout Configuration Methods ---
    def stack(self) -> StackManager:
        if self.__manager is not None:
            raise AppError("Manager already assigned!")
        self.__manager = StackManager(self.__stdscr)
        return self.__manager

    def multiplex(self, top_level_split_direction: Direction = Direction.horizontal) -> MultiplexManager:
        if self.__manager is not None:
            raise AppError("Manager already assigned!")
        self.__manager = MultiplexManager(self.__stdscr, top_level_split_direction)
        return self.__manager

    def new_panel(self, panel_type: type[PanelType], *mgr_args, **mgr_kwargs) -> PanelType:
        if self.__manager is None:
            raise AppError("No manager assigned!")
        
        new_panel = panel_type(region=rect2(0, 0, *self.__size), owner=self.__manager)
        self.__manager.add_panel(new_panel, *mgr_args, **mgr_kwargs)
        return new_panel

    # --- Input Handling Methods ---
    def set_control_handler(self, handler: typing.Callable[[int], typing.Any] | None):
        self.__control_handler = handler

    # --- Mainloop ---
    def run(self):
        _log.info("Running application")
        curses.set_escdelay(25)
        curses.raw()
        self.__stdscr.keypad(True)
        self.__stdscr.nodelay(True)

        if self.__manager is not None:
            self.__manager.arrange(self.__size)
            self.__manager.refresh()

        while self.__running:
            ch = self.__stdscr.getch()
            if ch == -1:
                continue
            elif ch == curses.KEY_RESIZE:
                if self.__manager is not None:
                    self.__manager.arrange(vec2(*self.__stdscr.getmaxyx()))
                    self.__manager.refresh()
            elif self.__control_handler:
                self.__control_handler(ch)

    def quit(self):
        self.__running = False

