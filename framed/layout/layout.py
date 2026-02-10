from abc import ABCMeta, abstractmethod
import curses

from ..struct import vec2
from ..widgets import Widget


class LayoutError(Exception):
    pass


class Layout(metaclass=ABCMeta):
    window_size: vec2

    def __init__(self):
        self.window_size = vec2()

    @abstractmethod
    def reset(self):
        """
        Resets the internal state of the layout. This includes
        any internal layout information, and any internal cached
        data produced by the bake() method. After calling reset(),
        a layout should be a blank slate.
        """
        raise NotImplementedError()

    @abstractmethod
    def bake(self):
        """
        Finalizes a layout for rendering. This method should
        do the heavy lifting of calculating the space that each
        widget should occupy, so that carve() can quickly and
        efficiently produce subwindows for each widget. This method
        should also call set_size() on the widgets which it manages.
        """
        raise NotImplementedError()

    @abstractmethod
    def carve(self, widget: Widget, window: curses.window) -> curses.window | None:
        """
        Produces a subwindow for a specified widget. If, for some reason, the
        layout could not allot space for the specified widget, this method returns
        None.
        """
        raise NotImplementedError()

