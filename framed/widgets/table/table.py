import enum
import typing

from .model import Model
from ...struct import vec2
from ..widget import FocusHolder


ModelType = typing.TypeVar("ModelType", bound=Model)


class Quadrant(enum.Enum):
    TL = enum.auto()
    TR = enum.auto()
    BL = enum.auto()
    BR = enum.auto()


class Connector(enum.Flag):
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

    __highlighted: typing.ClassVar[dict[str, str]] = {
        f"{L}-{Quadrant.TL}": '\u2578',
        f"{L}-{Quadrant.BL}": '\u2578',

        f"{T}-{Quadrant.TL}": '\u2579',
        f"{T}-{Quadrant.TR}": '\u2579',

        f"{R}-{Quadrant.TR}": '\u257A',
        f"{R}-{Quadrant.BR}": '\u257A',

        f"{B}-{Quadrant.BL}": '\u257B',
        f"{B}-{Quadrant.BR}": '\u257B',

        f"{LT}-{Quadrant.BL}": '\u2519',
        f"{LT}-{Quadrant.TL}": '\u251B',
        f"{LT}-{Quadrant.TR}": '\u251A',

        f"{LB}-{Quadrant.BL}": '\u2513',
        f"{LB}-{Quadrant.BR}": '\u2512',
        f"{LB}-{Quadrant.TL}": '\u2511',

        f"{LR}-{Quadrant.TR}": '\u257C',
        f"{LR}-{Quadrant.BR}": '\u257C',
        f"{LR}-{Quadrant.TL}": '\u257E',
        f"{LR}-{Quadrant.BL}": '\u257E',

        f"{TR}-{Quadrant.TR}": '\u2517',
        # TODO - finish
    }

    def emphasize(self, quadrant: Quadrant):
        return self.__class__.__highlighted.get(f"{self}-{quadrant}", self.regular)

    @property
    def regular(self) -> str:
        ...


class Table(FocusHolder, typing.Generic[ModelType]):
    __model: ModelType
    __selection: tuple[int, int] | None
    __column_widths: tuple[int, ...] | None

    def __init__(self, model_cls: type[ModelType]):
        super().__init__(greedy=True)
        self.__model = model_cls()
        self.__selection = None

    def set_size(self, size: vec2):
        super().set_size(size)
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
    def __render_begin(self):
        emphasize = self.__selection == (0, 0)
        self._window.addch('\u250F' if emphasize else '')

    def __render_end(self):
        ...

    def __render_row(self, row: int):
        ...

    def __render_line(self, line: int):
        if self.__column_widths is None:
            # there is not enough room!
            return

        if line == 0:
            self.__render_begin()
        elif line == (2 * self.__model.rows) + 1:
            self.__render_end()
        elif line % 2 == 1:
            self.__render_row(line // 2)

    def render(self):
        max_line = 2 * self.__model.rows + 1
        max_display_line = self.size[0] - 1
        for line in range(min(max_line, max_display_line)):
            self.__render_line(line)

