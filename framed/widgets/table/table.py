from __future__ import annotations
import curses
import enum
import typing

from .model import OutOfRangeError, TableModel
from ...struct import vec2
from ..widget import FocusHolder


ModelType = typing.TypeVar("ModelType", bound=TableModel)


class Quadrant(enum.Enum):
    TL = enum.auto()
    TR = enum.auto()
    BL = enum.auto()
    BR = enum.auto()


class Connector(enum.Flag):
    _ignore_ = ['_regular', '_highlighted']
    _regular: dict[Connector, str]
    _highlighted: dict[str, str]

    L = enum.auto()
    T = enum.auto()
    R = enum.auto()
    B = enum.auto()

    LT = L | T
    LB = L | B
    LR = L | R

    TR = T | R
    TB = T | B

    RB = R | B

    LTR = L | T | R
    LTB = L | T | B
    LRB = L | R | B
    TRB = T | R | B

    LTRB = L | T | R| B

    def emphasize(self, quadrant: Quadrant):
        return self.__class__._highlighted.get(f"{self}-{quadrant}", self.regular)

    @property
    def regular(self) -> str:
        return self.__class__._regular[self]


Connector._regular = {
    Connector.L: '\u2574',
    Connector.T: '\u2575',
    Connector.R: '\u2576',
    Connector.B: '\u2577',

    Connector.LT: '\u2518',
    Connector.LB: '\u2510',
    Connector.LR: '\u2500',
    Connector.TR: '\u2514',
    Connector.TB: '\u2502',
    Connector.RB: '\u250C',

    Connector.LTR: '\u2534',
    Connector.LTB: '\u2524',
    Connector.LRB: '\u252C',
    Connector.TRB: '\u251C',

    Connector.LTRB:  '\u253C',
}

Connector._highlighted = {
    f"{Connector.L}-{Quadrant.TL}": '\u2578',
    f"{Connector.L}-{Quadrant.BL}": '\u2578',

    f"{Connector.T}-{Quadrant.TL}": '\u2579',
    f"{Connector.T}-{Quadrant.TR}": '\u2579',

    f"{Connector.R}-{Quadrant.TR}": '\u257A',
    f"{Connector.R}-{Quadrant.BR}": '\u257A',

    f"{Connector.B}-{Quadrant.BL}": '\u257B',
    f"{Connector.B}-{Quadrant.BR}": '\u257B',

    f"{Connector.LT}-{Quadrant.BL}": '\u2519',
    f"{Connector.LT}-{Quadrant.TL}": '\u251B',
    f"{Connector.LT}-{Quadrant.TR}": '\u251A',

    f"{Connector.LB}-{Quadrant.BL}": '\u2513',
    f"{Connector.LB}-{Quadrant.BR}": '\u2512',
    f"{Connector.LB}-{Quadrant.TL}": '\u2511',

    f"{Connector.LR}-{Quadrant.TR}": '\u257C',
    f"{Connector.LR}-{Quadrant.BR}": '\u257C',
    f"{Connector.LR}-{Quadrant.TL}": '\u257E',
    f"{Connector.LR}-{Quadrant.BL}": '\u257E',

    f"{Connector.TR}-{Quadrant.TR}": '\u2517',
    f"{Connector.TR}-{Quadrant.BR}": '\u2515',
    f"{Connector.TR}-{Quadrant.TL}": '\u2516',

    f"{Connector.TB}-{Quadrant.TL}": '\u257F',
    f"{Connector.TB}-{Quadrant.TR}": '\u257F',
    f"{Connector.TB}-{Quadrant.BR}": '\u257D',
    f"{Connector.TB}-{Quadrant.BL}": '\u257D',

    f"{Connector.RB}-{Quadrant.BR}": '\u250F',
    f"{Connector.RB}-{Quadrant.TR}": '\u250D',
    f"{Connector.RB}-{Quadrant.BL}": '\u250E',

    f"{Connector.LTR}-{Quadrant.TL}": '\u2539',
    f"{Connector.LTR}-{Quadrant.TR}": '\u253A',
    f"{Connector.LTR}-{Quadrant.BR}": '\u2536',
    f"{Connector.LTR}-{Quadrant.BL}": '\u2535',
    
    f"{Connector.LTB}-{Quadrant.TL}": '\u2529',
    f"{Connector.LTB}-{Quadrant.TR}": '\u2526',
    f"{Connector.LTB}-{Quadrant.BR}": '\u2527',
    f"{Connector.LTB}-{Quadrant.BL}": '\u252A',

    f"{Connector.LRB}-{Quadrant.TL}": '\u252D',
    f"{Connector.LRB}-{Quadrant.TR}": '\u252E',
    f"{Connector.LRB}-{Quadrant.BR}": '\u2532',
    f"{Connector.LRB}-{Quadrant.BL}": '\u2531',

    f"{Connector.TRB}-{Quadrant.TL}": '\u251E',
    f"{Connector.TRB}-{Quadrant.TR}": '\u2521',
    f"{Connector.TRB}-{Quadrant.BR}": '\u2522',
    f"{Connector.TRB}-{Quadrant.BL}": '\u251F',

    f"{Connector.LTRB}-{Quadrant.TL}": '\u2543',
    f"{Connector.LTRB}-{Quadrant.TR}": '\u2544',
    f"{Connector.LTRB}-{Quadrant.BR}": '\u2546',
    f"{Connector.LTRB}-{Quadrant.BL}": '\u2545',
}


class DeletePolicy(enum.Enum):
    shift_previous = enum.auto()
    shift_next = enum.auto()
    deselect = enum.auto()


class Table(FocusHolder, typing.Generic[ModelType]):
    __model: ModelType
    __selection: tuple[int, int] | None
    __column_widths: tuple[int, ...] | None
    __offset: int

    def __init__(self, model_cls: type[ModelType]):
        super().__init__(greedy=True)
        self.__model = model_cls()
        self.__selection = None
        self.__column_widths = None
        self.__offset = 0

    # --- Overrides ---
    def set_size(self, size: vec2):
        super().set_size(size)
        self.__recalculate_columns()

    # --- Properties ---
    @property
    def selection(self) -> tuple[int, int] | None:
        return self.__selection

    @property
    def rows(self) -> int:
        return self.__model.rows

    @property
    def columns(self) -> int:
        return self.__model.columns

    # --- Table-specific Methods ---
    def set_selection(self, selection: tuple[int, int] | None):
        if self.__selection:
            base_row = (2 * self.__selection[0]) + 1
            invalidated_rows = {base_row - 1, base_row, base_row + 1}
        else:
            invalidated_rows = set()
        if selection is None:
            self.__selection = None
        elif (
            selection[0] < 0 or
            selection[0] >= self.__model.rows or
            selection[1] < 0 or
            selection[1] >= self.__model.columns
        ):
            raise OutOfRangeError(f"cell ({selection[0]}, {selection[1]}) out of range")
        else:
            self.__selection = selection
            base_row = (2 * selection[0]) + 1
            invalidated_rows.update({base_row - 1, base_row, base_row + 1})

        if self.__adjust_offset():
            self.invalidate()
        else:
            if self.request_update():
                for row in invalidated_rows:
                    self.__render_line(row)
                self._window.refresh()

    def set_cell_text(self, cell: tuple[int, int], text: str):
        self.__model.set_text(cell[0], cell[1], text)
        changed_line = 2 * cell[0] + 1
        if self.request_update():
            self.__render_line(changed_line)
            self._window.refresh()

    def set_cell_data(self, cell: tuple[int, int], data: typing.Any):
        self.__model.set_data(cell[0], cell[1], data)
        changed_line = 2 * cell[0] + 1
        if self.request_update():
            self.__render_line(changed_line)
            self._window.refresh()

    def set_rows(self, rows: int):
        self.__model.set_rows(rows)
        self.__recalculate_rows()
        self.__adjust_selection()

    def set_columns(self, cols: int):
        self.__model.set_columns(cols)
        self.__recalculate_columns()
        self.__adjust_selection()
        self.invalidate()

    def delete_row(self, row: int, policy: DeletePolicy = DeletePolicy.deselect):
        self.__model.delete_row(row)
        self.__recalculate_rows()

        if self.__selection is not None:
            sel_row, sel_col = self.__selection
            if sel_row == row:
                match policy:
                    case DeletePolicy.deselect:
                        self.__selection = None
                    case DeletePolicy.shift_previous:
                        new_row = max(0, sel_row - 1)
                        self.__selection = new_row, sel_col
                    case DeletePolicy.shift_next:
                        new_row = min(self.rows - 1, sel_row + 1)
                        self.__selection = new_row, sel_col
            elif sel_row > row:
                self.__selection = sel_row - 1, sel_col

        self.invalidate()

    def delete_column(self, col: int, policy: DeletePolicy = DeletePolicy.deselect):
        self.__model.delete_column(col)
        self.__recalculate_columns()

        if self.__selection is not None:
            sel_row, sel_col = self.__selection
            if sel_col == col:
                match policy:
                    case DeletePolicy.deselect:
                        self.__selection = None
                    case DeletePolicy.shift_previous:
                        new_col = max(0, sel_col - 1)
                        self.__selection = sel_row, new_col
                    case DeletePolicy.shift_next:
                        new_col = min(self.columns - 1, sel_col + 1)
                        self.__selection = sel_row, new_col
            elif sel_col > col:
                self.__selection = sel_row, sel_col - 1

        self.invalidate()

    def __adjust_selection(self):
        if self.__selection is None:
            return

        row, col = self.__selection
        if row >= self.rows:
            row = max(0, self.rows - 1)
        if col >= self.columns:
            col = max(0, self.columns - 1)

        row_changed = row != self.__selection[0]
        self.__selection = row, col
        if row_changed and self.request_update():
            self.__render_row(row)
            self._window.refresh()

    def __adjust_offset(self) -> bool:
        if self.__selection is not None:
            sel_row = self.__selection[0] * 2 + 1
            if self.__offset > sel_row:
                self.__offset = sel_row - 1
                return True
            elif self.__offset + self.size[0] - 1 < sel_row:
                new_bottom = sel_row + 2
                self.__offset = max(0, new_bottom - self.size[0])
                return True

        return False

    def __recalculate_rows(self):
        height = 2 * self.__model.rows + 1
        if self.__offset + self.size[0] >= height:
            self.__offset = max(0, height - self.size[0])
            self.invalidate()

    def __recalculate_columns(self):
        size = self.size
        total_width = size.x - (self.__model.columns + 1)
        if total_width < self.__model.columns:
            self.__column_widths = None
        else:
            widths = [total_width // self.__model.columns] * self.__model.columns
            consumed = sum(widths)
            index = 0
            while consumed < total_width:
                widths[index] += 1
                consumed += 1
                index += 1
            self.__column_widths = tuple(widths)

    # --- Widget Implementation ---
    def __render_row(self, row: int):
        if self.__column_widths is None:
            return

        target = (2 * row) + 1 - self.__offset
        self._window.move(target, 0)
        is_sel_row = self.__selection is not None and row == self.__selection[0]
        sel_col = self.__selection[1] if self.__selection is not None else -2
        col_index = 0
        for col_index, col in enumerate(self.__column_widths):
            border = '\u2503' if (is_sel_row and col_index in [sel_col, sel_col + 1]) else '\u2502'
            self._window.addch(border)
            content = self.__model.get_text(row, col_index)
            content = content.ljust(col, " ")
            self._window.addnstr(content, col)

        # render far-end border
        border = '\u2503' if is_sel_row and col_index == sel_col else '\u2502'
        try:
            self._window.addch(border)
        except curses.error:
            # NOTE: addch() can raise curses error in the bottom-right corner, even if render is successful
            pass

    def __render_separator(self, row: int):
        if self.__column_widths is None:
            return

        target = 2 * row - self.__offset
        self._window.move(target, 0)
        is_above_sel_row = self.__selection is not None and row == self.__selection[0]
        is_below_sel_row = self.__selection is not None and row == self.__selection[0] + 1
        sel_col = self.__selection[1] if self.__selection is not None else -2
        col_index = 0
        for col_index, col in enumerate(self.__column_widths):
            if col_index == 0 and row == 0:
                connector = Connector.RB
            elif col_index == self.__model.columns:
                connector = Connector.LB
            elif col_index == 0 and row == self.__model.rows:
                connector = Connector.TR
            elif col_index == 0:
                connector = Connector.TRB
            elif row == self.__model.rows:
                connector = Connector.LTR
            elif row == 0:
                connector = Connector.LRB
            else:
                connector = Connector.LTRB

            quadrant = None
            if is_above_sel_row:
                if col_index == sel_col:
                    quadrant = Quadrant.BR
                elif col_index == sel_col + 1:
                    quadrant = Quadrant.BL
            elif is_below_sel_row:
                if col_index == sel_col:
                    quadrant = Quadrant.TR
                elif col_index == sel_col + 1:
                    quadrant = Quadrant.TL

            self._window.addch(connector.emphasize(quadrant) if quadrant is not None else connector.regular)
            self._window.addnstr(('\u2501' if (is_above_sel_row or is_below_sel_row) and col_index == sel_col else '\u2500') * col, col)

        if row == 0:
            connector = Connector.LB
        elif row == self.__model.rows:
            connector = Connector.LT
        else:
            connector = Connector.LTB

        quadrant = None
        if col_index == sel_col:
            if is_above_sel_row:
                quadrant = Quadrant.BL
            elif is_below_sel_row:
                quadrant = Quadrant.TL

        try:
            self._window.addch(connector.emphasize(quadrant) if quadrant is not None else connector.regular)
        except curses.error:
            # NOTE: addch() can raise curses error in the bottom-right corner, even if render is successful
            pass

    def __render_line(self, line: int):
        if self.__column_widths is None:
            # there is not enough room!
            return

        if line < self.__offset or line > self.__offset + self.size[0] - 1:
            return

        if line % 2 == 1:
            self.__render_row(line // 2)
        else:
            self.__render_separator(line // 2)

    def render(self):
        max_line = 2 * self.__model.rows + 1
        max_display_line = self.__offset + self.size[0]
        for line in range(self.__offset, min(max_line, max_display_line)):
            self.__render_line(line)

    def on_focus(self):
        ...

    def on_unfocus(self):
        ...

    def on_input(self, ch: int) -> bool:
        ...

