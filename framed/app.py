import asyncio
import curses
import enum
import inspect
import time
import traceback
import typing
import weakref

from . import manager
from .context import Context
from .manager import Manager, StackManager, MultiplexManager, Direction
from .panel import FreePanel, Panel
from .struct import rect2, vec2
from .widgets import FocusHolder
from . import clock
from . import event
from . import task
from . import _log


PanelType = typing.TypeVar("PanelType", bound=Panel)
FreePanelType = typing.TypeVar("FreePanelType", bound=FreePanel)


class AppError(Exception):
    pass


class FocusCapture(enum.Enum):
    capture = 0
    passthrough = 1
    uncaught = 2


class FocusState:
    __focused: FocusHolder | None
    __keep: int | None
    def __init__(self):
        self.__focused = None
        self.__keep = None

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

        if self.__keep is not None:
            self.__keep = curses.curs_set(0)

    def capture_input(self, ch: int) -> FocusCapture:
        if self.__focused is not None and self.__focused.greedy:
            consumed = self.__focused.on_input(ch)
            if consumed:
                return FocusCapture.capture
            else:
                return FocusCapture.passthrough

        return FocusCapture.uncaught

    def on_input(self, ch: int):
        if self.__focused is not None:
            self.__focused.on_input(ch)

    def update(self):
        if self.__focused and not self.__focused.focused:
            self.__focused.on_unfocus()
            self.__focused = None

    def check(self):
        if self.__focused is not None:
            root = self.__focused.get_root()
            if root is None or not root.owned:
                self.__focused._focused = False
                self.__focused = None

    def keep(self):
        if self.__focused:
            self.__keep = curses.curs_set(0)

    def restore(self):
        if self.__keep is not None:
            curses.curs_set(self.__keep)
            if self.__focused:
                self.__focused.on_focus()
                self.__focused.invalidate()


InputHandler = typing.Callable[[int], FocusCapture | None]
TaskCallback = typing.Callable[[int, task.TaskStatus, typing.Any], typing.Any]
T = typing.TypeVar("T", bound=Context)


class App(typing.Generic[T]):
    __stdscr: curses.window
    __size: vec2

    __running: bool
    __manager: Manager | None
    __focus: FocusState
    __control_handler: InputHandler | None
    __context: T
    __clock: clock.Clock
    __tick_handlers: weakref.WeakSet[clock.TickHandler]

    __tasks: task.TaskManager

    def __init__(self, stdscr: curses.window, context_cls: type[T] = Context):
        self.__stdscr = stdscr
        self.__size = vec2(*stdscr.getmaxyx())
        self.__running = True
        self.__manager = None
        self.__focus = FocusState()
        self.__control_handler = None
        self.__context = context_cls()
        self.__clock = clock.Clock()
        self.__tick_handlers = weakref.WeakSet()
        self.__tasks = task.TaskManager()

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
        
        new_panel = panel_type(region=rect2(0, 0, *self.__size), owner=self.__manager, root=self)
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

    # --- Free Panels (Dialogs) ---
    def new_free_panel(self, panel_type: type[FreePanelType], region: rect2) -> FreePanelType:
        if self.__manager is None:
            raise AppError("No manager assigned!")

        new_panel = panel_type(region=region, owner=self.__manager, root=self)
        self.__manager.add_free_panel(new_panel)
        return new_panel

    def destroy_free_panel(self, panel: FreePanel):
        if self.__manager is None:
            raise AppError("No manager assigned!")

        self.__manager.remove_free_panel(panel)

    # --- Utilities ---
    def get_centered_region(self, h: int, w: int) -> rect2:
        if self.__manager is None:
            raise AppError("No manager assigned!")

        return self.__manager.get_centered_region(h, w)

    # --- Concurrency ---
    def task(self, fn: typing.Callable, fn_args: tuple | None = None, fn_kwargs: dict[str, typing.Any] | None = None) -> task.Task:
        fn_args = fn_args or ()
        fn_kwargs = fn_kwargs or {}
        if inspect.iscoroutinefunction(fn):
            return self.__tasks.dispatch_coroutine(fn(*fn_args, **fn_kwargs))
        elif inspect.isasyncgenfunction(fn):
            return self.__tasks.dispatch_generator(fn(*fn_args, **fn_kwargs))
        elif inspect.isfunction(fn):
            threaded = asyncio.to_thread(fn, *fn_args, **fn_kwargs)
            return self.__tasks.dispatch_coroutine(threaded)
        else:
            raise TypeError("fn must be a coroutine function, an async generator, or a regular function.")

    def __update_tasks(self):
        for task in self.__tasks.iter_complete():
            try:
                task.fulfill()
            except BaseException as exc:
                _log.error("".join(traceback.format_exception(exc)))

    # --- Clock ---
    def add_tick_handler(self, handler: clock.TickHandler):
        self.__tick_handlers.add(handler)

    def remove_tick_handler(self, handler: clock.TickHandler) -> bool:
        if handler in self.__tick_handlers:
            self.__tick_handlers.remove(handler)
            return True
        return False

    # --- Mainloop ---
    def run(self):
        _log.info("Running application")
        curses.set_escdelay(25)
        curses.raw()
        curses.curs_set(0)
        self.__stdscr.keypad(True)
        self.__stdscr.nodelay(True)

        if self.__manager is not None:
            self.__manager.set_screen_size(self.__size)
            self.__manager.refresh()

        self.__clock.start()
        try:
            while self.__running:
                time.sleep(0.05)
                self.__clock.update(self.__tick)

                self.__update_tasks()
                manager_flags = self.__manager.check_flags() if self.__manager else 0
                if (manager_flags & manager.FLAG_CHECK_FOCUS) != 0:
                    self.__focus.check()
                self.__focus.update()

                event.process_events()

                ch = self.__stdscr.getch()
                if ch == -1:
                    continue
                elif ch == 3:
                    self.quit()
                elif ch == curses.KEY_RESIZE:
                    if self.__manager is not None:
                        self.__size = vec2(*self.__stdscr.getmaxyx())
                        self.__focus.keep()
                        self.__manager.set_screen_size(self.__size)
                        self.__manager.refresh()
                        self.__focus.restore()
                        continue

                captured = self.__focus.capture_input(ch)
                if captured == FocusCapture.capture:
                    continue

                if self.__control_handler:
                    result = self.__control_handler(ch)
                    if result is FocusCapture.capture:
                        continue

                if captured == FocusCapture.uncaught:
                    self.__focus.on_input(ch)
        finally:
            self.__tasks.close()

    def __tick(self, dt: int):
        for handler in self.__tick_handlers:
            handler.on_tick(dt)

    def quit(self):
        self.__running = False

    @property
    def context(self) -> T:
        return self.__context

