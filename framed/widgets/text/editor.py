import enum
import functools
import typing

from ..widget import CursorMode, FocusHolder
from . import model

from ... import keys


T = typing.TypeVar("T", bound=model.TextModel)


class EditorMode(enum.Enum):
    command = 0
    edit = 1


class EditorAction(enum.Enum):
    nav_left = "nav_left"
    nav_right = "nav_right"
    nav_up = "nav_up"
    nav_down = "nav_down"

    edit_finish = "edit_finish"
    edit_backspace = "edit_backspace"
    edit_delete = "edit_delete"
    edit_linefeed = "edit_linefeed"

    @functools.cached_property
    def category(self) -> str:
        return self.value.split("_")[0]

    @functools.cached_property
    def is_edit_action(self) -> bool:
        return self.category == "edit"

    @functools.cached_property
    def is_navigate_action(self) -> bool:
        return self.category == "nav"

    @functools.cached_property
    def is_command_action(self) -> bool:
        return self.category == "command"


# FIX: Replace calls to _repaint() with more efficient, line-specific
# redrawing methods when possible. Only _repaint() when necessary.
class Editor(FocusHolder):
    _DEFAULT_BINDINGS = {
        keys.LEFT: EditorAction.nav_left,
        keys.RIGHT: EditorAction.nav_right,
        keys.UP: EditorAction.nav_up,
        keys.DOWN: EditorAction.nav_down,

        keys.ESCAPE: EditorAction.edit_finish,
        keys.BACKSPACE: EditorAction.edit_backspace,
        keys.DELETE: EditorAction.edit_delete,
        keys.RETURN: EditorAction.edit_linefeed,
        keys.ENTER: EditorAction.edit_linefeed,
    }

    __model: model.TextModel
    __offset: tuple[int, int]
    __cursor: model.TextLocation
    __mode: EditorMode

    __bindings: dict[int, EditorAction]
    __command_count: int

    def __init__(self, text: str = "", model_cls: type[T] = model.SimpleTextModel):
        super().__init__(greedy=True)
        self.__model = model_cls(text=text)
        self.__offset = 0, 0
        self.scrollok = False
        self.__cursor = model.TextLocation(0, 0)
        self.__mode = EditorMode.command
        self.__bindings = Editor._DEFAULT_BINDINGS.copy()
        self.__command_count = 0

    def on_focus(self):
        if not self.has_commands:
            self.__mode = EditorMode.edit

        self.__adjust_offset()
        self.__position_cursor()
        self._window.refresh()
        self.cursor(CursorMode.light)

    def on_unfocus(self):
        self.cursor(CursorMode.hidden)

    def __insert(self, ch: int):
        # NOTE: This checks if the input character is an ASCII character.
        # Unicode support is intended in the future.
        if 32 <= ch <= 126:
            self.__cursor = self.__model.insert(self.__cursor, chr(ch)).after
            self.__adjust_offset()
            self._repaint()
            return True
        else:
            action = self.__bindings.get(ch)
            if action is None or not action.is_edit_action:
                return False

            match action:
                case EditorAction.edit_backspace:
                    previous = self.__model.traverse(self.__cursor, -1)
                    if previous is not None:
                        self.__model.delete(model.TextRange(previous, self.__cursor))
                        self.__cursor = previous
                        self.__adjust_offset()
                        self._repaint()
                        return True
                case EditorAction.edit_delete:
                    next_pos = self.__model.traverse(self.__cursor, 1)
                    if next_pos is not None:
                        self.__model.delete(model.TextRange(self.__cursor, next_pos))
                        self.__adjust_offset()
                        self._repaint()
                        return True
                case EditorAction.edit_linefeed:
                    try:
                        result = self.__model.insert(self.__cursor, "\n")
                        self.__cursor = result.after
                        self._repaint()
                        return True
                    except model.TextModelError:
                        return False
                case EditorAction.edit_finish:
                    self._relinquish()
                    return True

        return False

    def __navigate(self, ch: int) -> bool:
        action = self.__bindings.get(ch)
        if action is None or not action.is_navigate_action:
            return False

        match action:
            case EditorAction.nav_left:
                prev_pos = self.__model.traverse(self.__cursor, -1)
                if prev_pos is not None:
                    self.__cursor = prev_pos
                    self.__adjust_offset()
                    self._repaint()
                    return True
            case EditorAction.nav_right:
                next_pos = self.__model.traverse(self.__cursor, 1)
                if next_pos is not None:
                    self.__cursor = next_pos
                    self.__adjust_offset()
                    self._repaint()
                    return True
            case EditorAction.nav_up:
                next_pos = self.__cursor.clone()
                next_pos.line -= 1
                if next_pos.line >= 0:
                    next_pos.col = min(self.__model.get_line_length(next_pos.line), next_pos.col)
                    self.__cursor = next_pos
                    self.__adjust_offset()
                    self._repaint()
                    return True
            case EditorAction.nav_down:
                next_pos = self.__cursor.clone()
                next_pos.line += 1
                if next_pos.line < self.__model.lines:
                    next_pos.col = min(self.__model.get_line_length(next_pos.line), next_pos.col)
                    self.__cursor = next_pos
                    self.__adjust_offset()
                    self._repaint()
                    return True

        return False

    def __command(self, ch: int):
        pass

    def on_input(self, ch: int):
        if self.__mode == EditorMode.edit:
            handled = self.__insert(ch)
            # TODO: try to identify "stop edit" action
            if not handled:
                handled = self.__navigate(ch)
        else:
            handled = self.__navigate(ch)
            if not handled:
                self.__command(ch)
        
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

    def __position_cursor(self):
        window_pos = self.__cursor.line - self.__offset[0], self.__cursor.col - self.__offset[1]
        if (
            0 <= window_pos[0] < self.size[0] and
            0 <= window_pos[1] < self.size[1]
        ):
            self._window.move(*window_pos)

    def set_mode(self, mode: EditorMode):
        self.__mode = mode

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
            self.__position_cursor()

    # --- Bindings ---
    def bind(self, key: int, action: EditorAction):
        current = self.__bindings.get(key)
        is_command = current is not None and current.is_command_action
        if action.is_command_action and not is_command:
            self.__commands += 1
        elif not action.is_command_action and is_command:
            self.__commands -= 1

        self.__bindings[key] = action

    def unbind(self, key: int = -1, action: EditorAction | None = None):
        if key == -1 and action is None:
            raise ValueError("Must provide either a key code or an action.")
        if key != -1 and action is not None:
            raise ValueError("Must provide either a key code or an action, not both.")

        if key != -1:
            action = self.__bindings.get(key)
            if action is not None:
                if action.is_command_action:
                    self.__commands -= 1
                del self.__bindings[key]

        if action is not None:
            keys = list(self.__bindings.keys())
            for key in keys:
                self.__commands -= 1
                del self.__bindings[key]

    def unbind_all(self):
        self.__bindings.clear()
        self.__commands = 0

    def set_bindings(self, bindings: dict[int, EditorAction]):
        self.__bindings.clear()
        self.__bindings.update(bindings)
        self.__commands = sum(1 if action.is_command_action else 0 for action in self.__bindings.values())

    @property
    def has_commands(self) -> bool:
        return self.__command_count > 0

