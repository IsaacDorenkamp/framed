from __future__ import annotations
from abc import ABCMeta, abstractmethod
import curses
import typing

from .layout import Layout
from .layout.fixed import FixedLayout
from .layout.flex import FlexLayout
from .layout.grid import GridLayout
from .struct import rect2, vec2
from .widgets import Widget


class Panel(metaclass=ABCMeta):
    __window: curses.window
    __widgets: list[Widget]

    __size: vec2
    __position: vec2
    __layout: Layout
    __valid: bool
    __owner: Manager | None
    __bordered: bool

    def __init__(self, region: rect2, owner: Manager | None = None):
        self.__window = curses.newwin(*region.curses)
        self.__widgets = []
        self.__size, self.__position = region.decompose()
        self.__layout = FixedLayout()
        self.__valid = False
        self.__owner = owner
        self.__bordered = False

    def add(self, widget: Widget):
        widget._adopt(self)
        self.__widgets.append(widget)

    def reconfigure(self):
        if self.__bordered:
            size = vec2(max(0, self.__size.y - 2), max(0, self.__size.x - 2))
            offset = vec2(1, 1)
        else:
            size = self.__size
            offset = None
        self.__layout.window_size = size
        self.__layout.bake(offset=offset)
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
        # FIX: sometimes, a window may be so shaped that, no
        # matter the order of resizing and moving, a curses
        # error will always occur. Need to add logic to
        # mitigate this (perhaps resize to 1, 1 every time?)
        self.__window.resize(*self.__size)
        self.__window.mvwin(*self.__position)
        self.arrange()
        self.reconfigure()
        self.__valid = True

    def render(self):
        if not self.__valid:
            self.__validate()

        self.__window.erase()
        if self.__bordered:
            self.__window.box()
        for widget in self.__widgets:
            if widget.windowed:
                widget.paint()
        self.__window.noutrefresh()

    # layout utilities
    def fixed(self) -> FixedLayout:
        if not isinstance(self.__layout, FixedLayout):
            self.__layout = FixedLayout()

        self.__layout.reset()
        return self.__layout

    def flex(self) -> FlexLayout:
        if not isinstance(self.__layout, FlexLayout):
            self.__layout = FlexLayout()

        self.__layout.reset()
        return self.__layout

    def grid(self) -> GridLayout:
        if not isinstance(self.__layout, GridLayout):
            self.__layout = GridLayout()

        self.__layout.reset()
        return self.__layout

    def request_update(self) -> bool:
        if self.__owner is not None:
            return self.__owner.request_update(self)

        return False

    def blit(self):
        # force window to redraw
        self.__window.touchwin()
        self.__window.refresh()

    @property
    def size(self) -> vec2:
        return self.__size

    @property
    def position(self) -> vec2:
        return self.__position

    @property
    def bordered(self) -> bool:
        return self.__bordered

    @bordered.setter
    def bordered(self, bordered: bool):
        self.__bordered = bordered
        self.__valid = False
        if self.request_update():
            self.render()
            curses.doupdate()

    @property
    def _owner(self) -> Manager:
        if self.__owner is None:
            raise ValueError("Owner is unset!")
        return self.__owner

    @property
    def owned(self) -> bool:
        return self.__owner is not None

    def _orphan(self):
        self.__owner = None

    def _adopt(self, owner: Manager):
        self.__owner = owner


class FreePanel(Panel):
    @abstractmethod
    def reposition(self, size: vec2):
        """
        Called when the application resizes, allowing
        free panels to position themselves within the
        new screen.
        """
        raise NotImplementedError()

    def close(self):
        if self.owned:
            self._owner.remove_free_panel(self)


if typing.TYPE_CHECKING:
    from .manager import Manager
