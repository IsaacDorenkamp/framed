from abc import ABCMeta, abstractmethod
import curses

from .struct import vec2


class Widget(metaclass=ABCMeta):
    _win: curses.window
    _abs_pos: vec2
    _rel_pos: vec2
    _size: vec2

    _parent: Container | None
    _valid: bool

    def __init__(self, root: curses.window, pos: vec2, size: vec2, parent: Container | None = None):
        self._parent = parent

        if parent is None:
            self._rel_pos = pos
            self._abs_pos = pos
        else:
            self._rel_pos = pos
            self._abs_pos = pos + parent.absolute_pos

        self._size = size
        self._win = root.subwin(*self._abs_pos, *self._size)
        self._valid = True

    @abstractmethod
    def render(self, window: curses.window):
        pass

    @property
    def absolute_pos(self) -> vec2:
        return self._abs_pos

    @property
    def relative_pos(self) -> vec2:
        return self._rel_pos

    def set_absolute_pos(self, pos: vec2):
        self._set_absolute_pos(pos, True)

    def set_relative_pos(self, pos: vec2):
        self._rel_pos = pos
        if self._parent is None:
            self._abs_pos = pos
        else:
            self._abs_pos = self._parent.absolute_pos + pos
        self._win.mvwin(*self._abs_pos)

    def _set_absolute_pos(self, pos: vec2, update_rel: bool):
        self._abs_pos = pos
        if update_rel:
            if self._parent is None:
                self._rel_pos = pos
            else:
                self._rel_pos = pos - self._parent.absolute_pos
        self._win.mvwin(*self._abs_pos)
        self.invalidate()

    def invalidate(self):
        self._valid = False

    def revalidate(self):
        # TODO: implement
        pass

class Container(Widget):
    _children: list[Widget]

    def __init__(self, root: curses.window, pos: vec2, size: vec2, parent: Container | None = None):
        super().__init__(root, pos, size, parent=parent)
        self._children = []

    def add(self, widget: Widget):
        self._children.append(widget)
        self.invalidate()

    def remove(self, widget: Widget):
        self._children.remove(widget)
        self.invalidate()

