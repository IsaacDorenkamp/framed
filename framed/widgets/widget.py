from __future__ import annotations
from abc import ABCMeta, abstractmethod
import curses
import functools
import typing

from ..struct import vec2


class WidgetError(Exception):
    pass


class Widget(metaclass=ABCMeta):
    __window: curses.window | None
    __size: vec2
    __parent: Panel | Widget | None

    def __init__(self):
        self.__window = None
        self.__size = vec2()
        self.__parent = None

    def enwindow(self, window: curses.window):
        if self.__window is not None:
            raise WidgetError("Widget is already windowed!")

        self.__window = window

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

    def _repaint(self):
        self._window.erase()
        self.render()
        self._window.refresh()

    @property
    def size(self) -> vec2:
        return self.__size

    def set_size(self, size: vec2):
        self.__size = size

    def request_update(self) -> bool:
        if self.__parent is not None:
            return self.__parent.request_update()

        return False

    def _adopt(self, parent: Panel | Widget):
        self.__parent = parent

    def _orphan(self):
        self.__parent = None

def invalidate(method: typing.Callable[..., bool]):
    @functools.wraps(method)
    def with_invalidate(self, *args, **kwargs):
        should_invalidate = method(self, *args, **kwargs)
        if should_invalidate and self.windowed is not None and self.request_update():
            self._repaint()

    return with_invalidate

if typing.TYPE_CHECKING:
    from ..panel import Panel
