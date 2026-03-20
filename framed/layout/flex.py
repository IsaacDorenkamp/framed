from collections import defaultdict
import curses
from dataclasses import dataclass, field

from .layout import Layout
from ..struct import rect2, vec2
from ..widgets import Widget
from .. import util


@dataclass
class _FlexItem:
    weight: int
    widget: Widget | None


@dataclass
class _FlexRow:
    weight: int = 0
    items: list[_FlexItem] = field(default_factory=list)


class FlexLayout(Layout):
    __rows: defaultdict[int, _FlexRow]
    __regions: dict[Widget, rect2]

    def __init__(self):
        super().__init__()
        self.__rows = defaultdict(_FlexRow)
        self.__regions = {}

    def add(self, widget: Widget, row: int, weight: int = 0):
        self.__rows[row].items.append(_FlexItem(weight=weight, widget=widget))

    def add_spacer(self, row: int, weight: int = 0):
        self.__rows[row].items.append(_FlexItem(weight=weight, widget=None))

    def set_row_weight(self, row: int, weight: int):
        self.__rows[row].weight = weight

    def reset(self):
        self.__rows.clear()
        self.__regions.clear()

    def bake(self, offset: vec2 | None = None):
        if offset is None:
            offset = vec2()

        total_rows = max(self.__rows.keys()) + 1  # rows start at 0
        row_minimums = [max([item.widget.min_size.y if item.widget else 1 for item in self.__rows[index].items] or [1]) if index in self.__rows else 1 for index in range(total_rows)]
        row_weights = [(self.__rows[row].weight if row in self.__rows else 0) for row in range(total_rows)]
        row_heights = util.distribute(self.window_size.y, row_weights, row_minimums)

        y_offset = offset.y
        for row, height in enumerate(row_heights):
            row_info = self.__rows.get(row)
            if row_info is None:
                y_offset += height
                continue

            column_weights = [item.weight for item in row_info.items]
            minimums = [item.widget.min_size.x if item.widget else 1 for item in row_info.items]
            column_widths = util.distribute(self.window_size.x, column_weights, minimums)
            x_offset = offset.x
            for column, item in enumerate(row_info.items):
                width = column_widths[column]
                if item.widget is not None:
                    self.__regions[item.widget] = rect2(y=y_offset, x=x_offset, h=height, w=width)
                    item.widget.set_size(vec2(height, width))
                x_offset += width
            y_offset += height

    def carve(self, widget: Widget, window: curses.window) -> curses.window | None:
        entry = self.__regions.get(widget)
        if entry is None or entry.w == 0 or entry.h == 0:
            return None

        return window.derwin(*entry.curses)

