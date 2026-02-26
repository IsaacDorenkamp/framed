import curses
import enum
import typing

from .manager import Manager, StackManager, MultiplexManager, Direction
from .panel import Panel
from .struct import rect2, vec2
from .widgets import FocusHolder
from . import _log


PanelType = typing.TypeVar("PanelType", bound=Panel)


class AppError(Exception):
    pass


class FocusCapture(enum.Enum):
    capture = 0
    passthrough = 1


class FocusState:
    __focused: FocusHolder | None
    def __init__(self):
        self.__focused = None

    def set_focused(self, focused: FocusHolder | None):
        if focused == self.__focused:
            return

        if self.__focused is not None:
            self.__focused._focused = False
            self.__focused.on_unfocus()
        self.__focused = focused
        if self.__focused is not None:
            self.__focused._focused = True
            self.__focused.on_focus()

    def capture_input(self, ch: int) -> bool:
        if self.__focused is not None:
            if self.__focused.greedy:
                self.__focused.on_input(ch)
                return True

        return False

    def on_input(self, ch: int):
        if self.__focused is not None:
            self.__focused.on_input(ch)

    def update(self):
        if self.__focused and not self.__focused.focused:
            self.__focused.on_unfocus()
            self.__focused = None


InputHandler = typing.Callable[[int], FocusCapture | None]


class App:
    __stdscr: curses.window
    __size: vec2

    __running: bool
    __manager: Manager | None
    __focus: FocusState
    __control_handler: InputHandler | None

    def __init__(self, stdscr: curses.window):
        self.__stdscr = stdscr
        self.__size = vec2(*stdscr.getmaxyx())
        self.__running = True
        self.__manager = None
        self.__focus = FocusState()
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

    # --- Focus Management ---
    def focus(self, holder: FocusHolder):
        if not holder.windowed:
            raise AppError("Cannot focus widget which is not displayed!")
        self.__focus.set_focused(holder)

    def clear_focus(self):
        self.__focus.set_focused(None)

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
            self.__focus.update()

            ch = self.__stdscr.getch()
            if ch == -1:
                continue
            elif ch == 3:
                # TODO: Allow user to disable this
                self.quit()
                continue
            elif ch == curses.KEY_RESIZE:
                if self.__manager is not None:
                    self.__manager.arrange(vec2(*self.__stdscr.getmaxyx()))
                    self.__manager.refresh()
                    continue

            captured = self.__focus.capture_input(ch)
            if captured:
                continue

            if self.__control_handler:
                result = self.__control_handler(ch)
                if result is FocusCapture.capture:
                    continue

            self.__focus.on_input(ch)

    def quit(self):
        self.__running = False

