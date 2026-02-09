from abc import ABCMeta
import curses

from .layout import Layout
from .struct import rect2, vec2
from .widget import Widget


class Panel(metaclass=ABCMeta):
    __window: curses.window
    __widgets: list[Widget]

    __size: vec2
    __position: vec2
    __layout: Layout

    def __init__(self, region: rect2):
        self.__window = curses.newwin(*region.curses)
        self.__widgets = []
        self.__size, self.__position = region.decompose()
        self.__layout = Layout()  # TODO: this is going to be abstract

    def add(self, widget: Widget):
        self.__widgets.append(widget)

    def reconfigure(self):
        self.__layout.reset()
        self.__layout.window_size = self.__size
        for widget in self.__widgets:
            widget.dewindow(erase=False)
            window = self.__layout.carve(widget, self.__window)
            if window is not None:
                widget.enwindow(window)

        self.__window.erase()
        for widget in self.__widgets:
            widget.render()
        self.__window.refresh()

    @property
    def size(self) -> vec2:
        return self.__size

    @property
    def position(self) -> vec2:
        return self.__position

