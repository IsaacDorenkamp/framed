from abc import ABCMeta, abstractmethod
import curses

from ..struct import vec2
from ..widget import Widget

class Layout(metaclass=ABCMeta):
    window_size: vec2

    def __init__(self):
        self.window_size = vec2()

    @abstractmethod
    def reset(self):
        raise NotImplementedError()

    @abstractmethod
    def carve(self, widget: Widget, window: curses.window) -> curses.window:
        raise NotImplementedError()

