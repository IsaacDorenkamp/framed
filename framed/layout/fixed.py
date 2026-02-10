import curses

from .layout import Layout, LayoutError
from ..struct import rect2, vec2
from ..widgets import Widget


class FixedLayout(Layout):
    __positions: dict[Widget, rect2]
    __constrained: dict[Widget, rect2]

    def __init__(self):
        self.__positions = {}
        self.__constrained = {}

    def add(self, widget: Widget, y: int, x: int, height: int, width: int):
        if widget in self.__positions:
            raise LayoutError("cannot add widget to layout twice!")
        elif y < 0 or x < 0:
            raise LayoutError("y and x must be greater than 0!")
        elif height < 1 or width < 1:
            raise LayoutError("height and width must be at least 1!")
        self.__positions[widget] = rect2(y, x, height, width)

    def reset(self):
        self.__positions.clear()
        self.__constrained.clear()

    def bake(self):
        for widget, position in self.__positions.items():
            actual_y = min(position.y, self.window_size.y - 1)
            actual_x = min(position.x, self.window_size.x - 1)
            actual_end_y = min(actual_y + position.h - 1, self.window_size.y - 1)
            actual_end_x = min(actual_x + position.w - 1, self.window_size.x - 1)
            region = rect2(
                actual_y, actual_x, actual_end_y - actual_y + 1, actual_end_x - actual_x + 1
            )
            self.__constrained[widget] = region
            widget.set_size(vec2(region.h, region.w))

    def carve(self, widget: Widget, window: curses.window) -> curses.window | None:
        entry = self.__constrained.get(widget)
        if entry is None:
            return None

        return window.derwin(*entry.curses)

