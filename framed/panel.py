from abc import ABCMeta, abstractmethod
import curses

from .layout import Layout
from .layout.fixed import FixedLayout
from .layout.grid import GridLayout
from .struct import rect2, vec2
from .widgets import Widget

from . import _log


class Panel(metaclass=ABCMeta):
    __window: curses.window
    __widgets: list[Widget]

    __size: vec2
    __position: vec2
    __layout: Layout
    __valid: bool

    def __init__(self, region: rect2):
        self.__window = curses.newwin(*region.curses)
        self.__widgets = []
        self.__size, self.__position = region.decompose()
        self.__layout = FixedLayout()
        self.__valid = False

    def add(self, widget: Widget):
        self.__widgets.append(widget)

    def reconfigure(self):
        self.__layout.window_size = self.__size
        self.__layout.bake()
        for widget in self.__widgets:
            widget.dewindow(erase=False)
            window = self.__layout.carve(widget, self.__window)
            if window is not None:
                widget.enwindow(window)

    @abstractmethod
    def arrange(self):
        """
        Declare a layout, and place widgets inside it.
        """
        raise NotImplementedError()

    def set_size(self, size: vec2):
        self.__size = size
        self.__valid = False

    def set_position(self, position: vec2):
        self.__position = position
        self.__valid = False

    def __validate(self):
        self.__window.resize(*self.__size)
        self.__window.mvwin(*self.__position)
        self.arrange()
        self.reconfigure()
        self.__valid = True

    def render(self):
        if not self.__valid:
            self.__validate()

        self.__window.erase()
        for widget in self.__widgets:
            if widget.windowed:
                widget.render()
        self.__window.noutrefresh()

    # layout utilities
    def fixed(self) -> FixedLayout:
        if not isinstance(self.__layout, FixedLayout):
            self.__layout = FixedLayout()

        self.__layout.reset()
        return self.__layout

    def grid(self) -> GridLayout:
        if not isinstance(self.__layout, GridLayout):
            self.__layout = GridLayout()

        self.__layout.reset()
        return self.__layout

    @property
    def size(self) -> vec2:
        return self.__size

    @property
    def position(self) -> vec2:
        return self.__position

