import typing

from ..widget import CursorMode, FocusHolder
from . import model

from ... import keys
from ... import _log


T = typing.TypeVar("T", bound=model.TextModel)


class Editor(FocusHolder):
    __model: model.TextModel
    __offset: tuple[int, int]
    __cursor: model.TextLocation

    def __init__(self, text: str = "", model_cls: type[T] = model.SimpleTextModel):
        super().__init__(greedy=True)
        self.__model = model_cls(text=text)
        self.__offset = 0, 0
        self.scrollok = False
        self.__cursor = model.TextLocation(0, 0)

    def on_focus(self):
        self._window.move(0, 0)
        self._window.refresh()
        self.cursor(CursorMode.light)

    def on_unfocus(self):
        self.cursor(CursorMode.hidden)

    def on_input(self, ch: int):
        if 32 <= ch <= 126:
            # is ascii character
            screen_loc = self.__cursor.line - self.__offset[0], self.__cursor.col - self.__offset[1]
            self.__model.insert(self.__cursor, chr(ch))
            if screen_loc[1] == self.size[1] - 1:
                self.__shift_left()
            self._repaint()
            self._window.move(*screen_loc)
            self._window.refresh()
            self.__cursor.col += 1
        elif ch == keys.BACKSPACE:
            if self.__cursor.col > 0:
                prev_loc = model.TextLocation(line=self.__cursor.line, col=self.__cursor.col - 1)
                self.__model.delete(model.TextRange(prev_loc, prev_loc))
                self.__cursor.col -= 1
                self._repaint()
            elif self.__cursor.line > 0:
                prev_line_length = self.__model.get_line_length(self.__cursor.line - 1)
                self.__model.delete(
                    model.TextRange(
                        model.TextLocation(line=self.__cursor.line - 1, col=prev_line_length-1),
                        model.TextLocation(line=self.__cursor.line - 1, col=prev_line_length)
                    )
                )
                self._repaint()
        elif ch == keys.DELETE:
            self.__model.delete(model.TextRange(self.__cursor, self.__cursor))
            self._repaint()

    def __shift_left(self):
        self.__offset = self.__offset[0], self.__offset[1] + 1

    def render(self):
        end_line = min(self.__offset[0] + self.size[0], self.__model.lines)
        for line_no in range(self.__offset[0], end_line):
            window_line = line_no - self.__offset[0]
            length = self.__model.get_line_length(line_no)
            end = min(length - 1, self.__offset[1] + self.size[1] - 1)
            if self.__offset[1] > end:
                continue
            line = self.__model.get(
                model.TextRange(
                    model.TextLocation(line=window_line, col=self.__offset[1]),
                    model.TextLocation(line=window_line, col=end)
                )
            )
            self._window.move(window_line, 0)
            self._window.addnstr(line, self.size[1])

        if self.focused:
            # TODO: move to cursor loc
            pass

