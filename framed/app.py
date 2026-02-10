import curses
import typing

from .manager import Manager, StackManager
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

    def __init__(self, stdscr: curses.window):
        self.__stdscr = stdscr
        self.__size = vec2(*stdscr.getmaxyx())
        self.__running = True
        self.__manager = None

    def stack(self) -> StackManager:
        if self.__manager is not None:
            raise AppError("Manager already assigned!")
        self.__manager = StackManager(self.__stdscr)
        return self.__manager

    def new_panel(self, panel_type: type[PanelType], *mgr_args, **mgr_kwargs):
        if self.__manager is None:
            raise AppError("No manager assigned!")
        
        new_panel = panel_type(rect2(0, 0, *self.__size))
        self.__manager.add_panel(new_panel, *mgr_args, **mgr_kwargs)

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
            elif ch == 3:
                # Ctrl-C
                self.__running = False
            elif ch == curses.KEY_RESIZE:
                if self.__manager is not None:
                    self.__manager.set_size(vec2(*self.__stdscr.getmaxyx()))
                    self.__manager.refresh()
            else:
                pass

