import typing

from ..widget import CursorMode, FocusHolder
from . import model

from ... import keys


T = typing.TypeVar("T", bound=model.TextModel)


class Editor(FocusHolder):
    __model: model.TextModel
    __ins_point: model.TextLocation | None
    __ins_buf: bytearray
    __offset: tuple[int, int]

    def __init__(self, model_cls: type[T] = model.SimpleTextModel):
        super().__init__(greedy=True)
        self.__model = model_cls()
        self.__ins_point = None
        self.__ins_buf = bytearray()
        self.__offset = 0, 0
        self.scrollok = False

    def on_focus(self):
        self._window.move(0, 0)
        self._window.refresh()
        self.cursor(CursorMode.light)

    def on_unfocus(self):
        self.cursor(CursorMode.hidden)

    def on_input(self, ch: int):
        if 32 <= ch <= 126:
            # is ascii character
            self.__ins_buf.append(ch)
            if self.request_update():
                self._window.addch(ch)
                self._window.refresh()
        elif ch in [keys.CR, keys.LF] and self.__ins_point:
            ins_str = self.__ins_buf.decode('ascii')
            self.__ins_buf.clear()
            self.__model.insert(self.__ins_point, ins_str)

    def render(self):
        end_line = min(self.__offset[0] + self.size[0], self.__model.lines - 1)
        for line_no in range(self.__offset[0], end_line):
            window_line = line_no - self.__offset[0]
            # TODO: finish

