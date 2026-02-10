import curses
from dataclasses import dataclass

from .layout import Layout, LayoutError
from ..struct import rect2, vec2
from ..widgets import Widget
from .. import _log


@dataclass(frozen=True)
class GridInfo:
    widget: Widget
    row_span: int
    col_span: int


class GridLayout(Layout):
    __cells: dict[vec2, GridInfo]
    __widgets: set[Widget]  # used to avoid iterating over cells to check for duplicates
    __regions: dict[Widget, rect2]

    def __init__(self):
        self.__cells = {}
        self.__widgets = set()
        self.__regions = {}

    def add(self, widget: Widget, row: int, col: int, row_span: int = 1, col_span: int = 1):
        if row_span < 1:
            raise LayoutError("row_span must be at least 1!")
        elif col_span < 1:
            raise LayoutError("col_span must be at least 1!")
        elif widget in self.__widgets:
            raise LayoutError("cannot add widget to layout twice!")

        self.__cells[vec2(row, col)] = GridInfo(widget, row_span, col_span)
        self.__widgets.add(widget)

    def reset(self):
        self.__cells.clear()
        self.__widgets.clear()
        self.__regions.clear()

    def bake(self):
        if not self.__cells:
            return

        max_row = max(pos.y + info.row_span - 1 for pos, info in self.__cells.items())
        max_col = max(pos.x + info.col_span - 1 for pos, info in self.__cells.items())
        num_rows = max_row + 1
        num_cols = max_col + 1
        for pos, info in self.__cells.items():
            row_height = (self.window_size.y * info.row_span) // num_rows
            col_width  = (self.window_size.x * info.col_span) // num_cols
            if row_height == 0 or col_width == 0:
                continue
            region = rect2(y=pos.y * row_height, x=pos.x * col_width, h=row_height, w=col_width)
            self.__regions[info.widget] = region
            info.widget.set_size(vec2(region.h, region.w))

    def carve(self, widget: Widget, window: curses.window) -> curses.window | None:
        entry = self.__regions.get(widget)
        if entry is None:
            return None

        return window.derwin(*entry.curses)

