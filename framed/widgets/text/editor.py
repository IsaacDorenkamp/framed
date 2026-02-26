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
            self.__model.insert(self.__cursor, chr(ch))
            self.__cursor.col += 1
            self.__adjust_offset()
            self._repaint()
        elif ch == keys.BACKSPACE:
            previous = self.__model.traverse(self.__cursor, -1)
            if previous is not None:
                self.__model.delete(
                    model.TextRange(
                        previous,
                        self.__cursor,
                    )
                )
                self.__cursor = previous
                self.__adjust_offset()
                self._repaint()
        elif ch == keys.DELETE:
            next_pos = self.__model.traverse(self.__cursor, 1)
            if next_pos is not None:
                self.__model.delete(model.TextRange(self.__cursor, next_pos))
                self.__adjust_offset()
                self._repaint()
        elif ch in [keys.ENTER, keys.RETURN]:
            try:
                result = self.__model.insert(self.__cursor, "\n")
                self.__cursor = result.after
                self._repaint()
            except model.TextModelError:
                # TODO: Give some indication of failure?
                _log.exception("Newline failed")
        elif ch == keys.LEFT:
            prev_pos = self.__model.traverse(self.__cursor, -1)
            if prev_pos is not None:
                self.__cursor = prev_pos
                self.__adjust_offset()
                self._repaint()
        elif ch == keys.RIGHT:
            next_pos = self.__model.traverse(self.__cursor, 1)
            if next_pos is not None:
                self.__cursor = next_pos
                self.__adjust_offset()
                self._repaint()
        elif ch == keys.UP:
            next_pos = self.__cursor.clone()
            next_pos.line -= 1
            if next_pos.line >= 0:
                next_pos.col = min(self.__model.get_line_length(next_pos.line), next_pos.col)
                self.__cursor = next_pos
                self.__adjust_offset()
                self._repaint()
        elif ch == keys.DOWN:
            next_pos = self.__cursor.clone()
            next_pos.line += 1
            if next_pos.line < self.__model.lines:
                next_pos.col = min(self.__model.get_line_length(next_pos.line), next_pos.col)
                self.__cursor = next_pos
                self.__adjust_offset()
                self._repaint()

    def __adjust_offset(self):
        """
        Update the view offset to ensure that the cursor is visible.
        """
        new_line, new_col = self.__offset

        diff_y_above = self.__offset[0] - self.__cursor.line
        diff_y_below = self.__cursor.line - (self.__offset[0] + self.size[0])
        if diff_y_above > 0:
            new_line = self.__offset[0] - diff_y_above
        elif diff_y_below > 0:
            new_line = self.__cursor.line - (self.__offset[0] + self.size[0])

        diff_x_left = self.__offset[1] - self.__cursor.col
        diff_x_right = self.__cursor.col - (self.__offset[1] + self.size[1]) + 1
        if diff_x_left > 0:
            new_col -= diff_x_left
        elif diff_x_right > 0:
            new_col += diff_x_right

        self.__offset = new_line, new_col

    def render(self):
        end_line = min(self.__offset[0] + self.size[0], self.__model.lines)
        for line_no in range(self.__offset[0], end_line):
            window_line = line_no - self.__offset[0]
            length = self.__model.get_line_length(line_no)
            end = min(length, self.__offset[1] + self.size[1] - 1)
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
            window_pos = self.__cursor.line - self.__offset[0], self.__cursor.col - self.__offset[1]
            if (
                0 <= window_pos[0] < self.size[0] and
                0 <= window_pos[1] < self.size[1]
            ):
                self._window.move(*window_pos)

