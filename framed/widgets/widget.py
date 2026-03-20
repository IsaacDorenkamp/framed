from __future__ import annotations
from abc import ABCMeta, abstractmethod
from collections import defaultdict
import curses
import enum
import functools
import typing
import warnings

from ..struct import vec2
from .. import palette


EventType = typing.TypeVar("EventType", bound="Event", contravariant=True)


class CursorMode(enum.IntEnum):
    hidden = 0
    light = 1
    visible = 2


class WidgetError(Exception):
    pass


class InvalidateMethod(typing.Protocol):
    def __call__(self, *args, **kwargs) -> bool: ...


class EventHandler(typing.Protocol, typing.Generic[EventType]):
    def __call__(self, event: EventType): ...


class Widget(metaclass=ABCMeta):
    __window: curses.window | None
    __size: vec2
    _parent: Panel | Widget | None
    __background: palette.ColorInfo
    __foreground: palette.ColorInfo
    __color_attr: int
    __scrollok: bool

    _valid: bool

    __enabled_events: list[str]
    __listeners: defaultdict[str, list[EventHandler]]

    def __init__(self, scrollok: bool = False, enabled_events: list[str] | None = None):
        self.__window = None
        self.__size = vec2()
        self._parent = None
        self.__background = palette.default_color_info
        self.__foreground = palette.default_color_info
        self.__color_attr = palette.color_pair(self.__background[0], self.__foreground[0])
        self.__scrollok = scrollok
        self._valid = False

        self.__enabled_events = enabled_events or []
        self.__listeners = defaultdict(list)

    def enwindow(self, window: curses.window):
        if self.__window is not None:
            raise WidgetError("Widget is already windowed!")

        window.scrollok(self.__scrollok)
        self.__window = window
        self._valid = False

    def dewindow(self, erase: bool = True):
        if self.__window is not None:
            if erase:
                self.__window.erase()
                self.__window.refresh()
            self.__window = None

    @property
    def windowed(self) -> bool:
        return self.__window is not None

    @property
    def _window(self) -> curses.window:
        if self.__window is None:
            raise WidgetError("Widget is not windowed!")

        return self.__window

    @abstractmethod
    def render(self):
        """
        Renders this widget from a completely blank slate.
        This method should not be called often, as widgets
        should be generally designed to perform minimal
        updates when their internal state changes, only
        performing complete re-renders when the entire
        state has been invalidated.
        """
        raise NotImplementedError()

    def paint(self):
        if not self._valid:
            self._validate()
            self._valid = True

        self.render()

    def _validate(self):
        self._window.bkgd(self.color_attr)

    def _repaint(self):
        self._window.erase()
        self.paint()
        self._window.refresh()

    @property
    def size(self) -> vec2:
        return self.__size

    def set_size(self, size: vec2):
        self.__size = size

    def request_update(self) -> bool:
        if self._parent is not None:
            return self.windowed and self._parent.request_update()

        return False

    def _adopt(self, parent: Panel | Widget):
        self._parent = parent

    def _orphan(self):
        self._parent = None

    # NOTE: While the default implementation simply calls window.bkgd()
    # this method is intended to allow implementation by subclasses to
    # more efficiently update the window's color if possible.
    def _update_colors(self):
        self._window.bkgd(self.color_attr)
        self._window.refresh()

    @property
    def background(self) -> str:
        return self.__background[0]

    @background.setter
    def background(self, color: str):
        self.__background = palette.validate(color)
        self.__color_attr = palette.color_pair(self.__foreground[0], self.__background[0])
        if self.request_update():
            self._update_colors()
        else:
            self._valid = False

    @property
    def foreground(self) -> str:
        return self.__foreground[0]

    @foreground.setter
    def foreground(self, color: str):
        self.__foreground = palette.validate(color)
        self.__color_attr = palette.color_pair(self.__foreground[0], self.__background[0])
        if self.request_update():
            self._update_colors()
        else:
            self._valid = False

    @property
    def color_attr(self) -> int:
        return self.__color_attr

    @property
    def scrollok(self) -> bool:
        return self.__scrollok

    @scrollok.setter
    def scrollok(self, scrollok: bool):
        self.__scrollok = scrollok
        if self.windowed:
            self._window.scrollok(scrollok)

    def cursor(self, mode: CursorMode):
        curses.curs_set(mode)

    def invalidate(self):
        if self.windowed and self.request_update():
            self._repaint()

    def get_root(self) -> Panel | None:
        current = self
        while isinstance(current, Widget):
            current = current._parent

        return current

    # --- Layout Preferences ---
    @property
    def min_size(self) -> vec2:
        """
        The minimum preferred size of the widget. Layouts will make an effort
        to keep a widget larger than, or equal to, this size; however, if this
        is not an absolute guarantee. Widgets should be designed to render
        without errors at any size, but it may be the case that it will appear
        incomplete or broken when smaller than this size.

        Further, if this value changes as a result of some other method (for
        example, set_text() on a Label), the layout will not automatically
        adjust. The developer must manually invoke the layout.
        """
        return vec2(1, 1)

    # --- Event Logic ---
    def listen(self, event_type: type[EventType], handler: EventHandler[EventType]):
        if event_type.tag not in self.__enabled_events:
            raise ValueError(f"{self.__class__.__name__} cannot handle {event_type.tag} events")

        self.__listeners[event_type.tag].append(handler)

    def unlisten(self, event_type: type[EventType], handler: EventHandler[EventType]) -> bool:
        entry = self.__listeners.get(event_type.tag)
        if entry is None:
            return False

        if handler in entry:
            entry.remove(handler)
            return True
        else:
            return False

    def _emit(self, event: Event):
        from ..event import queue_event
        queue_event(event)

    def _process(self, event: Event):
        if event.tag not in self.__enabled_events:
            warnings.warn(f"{self.__class__.__name__} should not emit {event.__class__.tag} events, but one has")

        entry = self.__listeners.get(event.__class__.tag)
        if entry is not None:
            for listener in entry:
                listener(event)


class FocusHolder(Widget):
    __greedy: bool
    _focused: bool
    def __init__(self, greedy: bool = True, scrollok: bool = False, enabled_events: list[str] | None = None):
        super().__init__(scrollok=scrollok, enabled_events=enabled_events)
        self.__greedy = greedy
        self._focused = False

    @abstractmethod
    def on_focus(self):
        raise NotImplementedError()

    @abstractmethod
    def on_unfocus(self):
        raise NotImplementedError()

    @abstractmethod
    def on_input(self, ch: int) -> bool:
        raise NotImplementedError()

    @property
    def focused(self) -> bool:
        return self._focused

    @property
    def greedy(self) -> bool:
        return self.__greedy

    def _relinquish(self):
        self._focused = False


def invalidator(method: InvalidateMethod):
    @functools.wraps(method)
    def with_invalidate(self, *args, **kwargs):
        should_invalidate = method(self, *args, **kwargs)
        if should_invalidate:
            self.invalidate()

    return with_invalidate

if typing.TYPE_CHECKING:
    from ..panel import Panel
    from ..event import Event

