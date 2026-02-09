from abc import ABCMeta, abstractmethod
import curses
from typing import Self

from .struct import vec2


class WidgetError(Exception):
    pass


class Widget(metaclass=ABCMeta):
    _window: curses.window | None
    __size: vec2

    def __init__(self):
        self._window = None
        self.__size = vec2()

    def repaint(self):
        """
        Clear this widget's window and render it from scratch.
        This method is expensive and should be avoided when
        possible.
        """
        if self._window is None:
            raise WidgetError("Widget is not windowed!")

        self._window.erase()
        self.render()
        self._window.refresh()

    def enwindow(self, window: curses.window):
        if self._window is not None:
            raise WidgetError("Widget is already windowed!")

        self._window = window

    def dewindow(self, erase: bool = True):
        if self._window is not None:
            if erase:
                self._window.erase()
                self._window.refresh()
            self._window = None

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

    @property
    def size(self) -> vec2:
        return self.__size

    def set_size(self, size: vec2):
        self.__size = size

