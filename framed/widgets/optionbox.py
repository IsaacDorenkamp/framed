import curses
from dataclasses import dataclass
import enum
import typing

from ..event.change import ChangeEvent
from .. import keys
from .widget import CursorMode, FocusHolder


T = typing.TypeVar("T")


class OptionBoxAction(enum.Enum):
    edit_cancel = "edit_cancel"
    edit_finish = "edit_finish"


@dataclass(frozen=True)
class OptionBoxChange(typing.Generic[T]):
    label: str
    index: int
    value: T | None


class OptionBox(FocusHolder, typing.Generic[T]):
    _DEFAULT_BINDINGS: typing.ClassVar[dict[int, OptionBoxAction]] = {
        keys.ESCAPE: OptionBoxAction.edit_cancel,
        keys.ENTER: OptionBoxAction.edit_finish,
        keys.RETURN: OptionBoxAction.edit_finish
    }

    __items: list[tuple[str, T | None]]
    __default: T | None
    __input: str
    __predicted: tuple[int, str] | None
    __selected: int
    __placeholder: str

    __bindings: dict[int, OptionBoxAction]

    def __init__(self):
        super().__init__(enabled_events=[ChangeEvent.tag])
        self.__items = []
        self.__default = None
        self.__input = ""
        self.__predicted = None
        self.__selected = -1
        self.__placeholder = "No Selection"

        self.__bindings = OptionBox._DEFAULT_BINDINGS.copy()

    # --- Events ---
    def __emit_change(self):
        if self.__selected == -1:
            change = OptionBoxChange(
                label=self.__placeholder,
                index=-1,
                value=None
            )
        else:
            selected = self.__items[self.__selected]
            change = OptionBoxChange(
                label=selected[0],
                index=self.__selected,
                value=selected[1],
            )
        self._emit(ChangeEvent(self, change))

    # --- Items ---
    def add_option(self, text: str, value: T | None = None):
        self.__items.append((text, value))

    def clear(self):
        if self.__default is not None:
            index = next((index for index, item in enumerate(self.__items) if item[1] == self.__default), None)
            if index is not None:
                self.__selected = index
                self.__emit_change()
                self.invalidate()
                return

        self.__selected = -1
        self.__emit_change()
        self.invalidate()

    @property
    def default(self) -> T | None:
        return self.__default

    @default.setter
    def default(self, default: T | None):
        if default is None:
            self.__default = None
            return

        # ensure there is an item with the given value
        index = next((index for index, item in enumerate(self.__items) if item[1] == default), None)
        if index is None:
            raise ValueError(f"No option has value '{default}'")

        self.__default = default

        if self.__selected == -1:
            self.__selected = index
            self.invalidate()

    @property
    def placeholder(self) -> str:
        return self.__placeholder

    @placeholder.setter
    def placeholder(self, placeholder: str):
        self.__placeholder = placeholder
        self.invalidate()

    # --- Widget Implementation ---
    def on_focus(self):
        self.cursor(CursorMode.light)
        self.__input = ""
        self.__predicted = None
        self._window.move(0, 0)
        self._window.clrtoeol()
        self._window.refresh()

    def on_unfocus(self):
        self.cursor(CursorMode.hidden)
        self.__input = ""
        self.__predicted = None
        self.invalidate()

    def on_input(self, ch: int):
        action = self.__bindings.get(ch)
        # bound actions should override input
        if action:
            match action:
                case OptionBoxAction.edit_cancel:
                    self.clear()
                case OptionBoxAction.edit_finish:
                    if self.__predicted:
                        self.__selected = self.__predicted[0]
                        self.__emit_change()
            self._relinquish()
            self.invalidate()
        elif 32 <= ch <= 126:
            letter = chr(ch)
            predictions = self.__predict(letter)
            if predictions:
                if len(predictions) > 1:
                    self.__input += letter
                    try:
                        self._window.addch(letter)
                    except curses.error:
                        pass
                    checkpoint = len(self.__input)
                    available = self.size[1] - checkpoint
                    self.__predicted = predictions[0]
                    remainder = self.__predicted[1][checkpoint:]
                    try:
                        self._window.addnstr(remainder, available, curses.A_DIM)
                    except curses.error:
                        pass
                    self._window.clrtoeol()
                    self._window.move(0, min(len(self.__input), self.size[1] - 1))
                    self._window.refresh()
                else:
                    # there is exactly one option, select it
                    self.__selected = predictions[0][0]
                    self._window.move(0, 0)
                    self._window.clrtoeol()
                    try:
                        self._window.addnstr(predictions[0][1], self.size[1])
                    except curses.error:
                        pass
                    self._window.clrtoeol()
                    self._window.refresh()
                    self.__emit_change()
                    self._relinquish()
            return True

        return False

    def __predict(self, added: str) -> list[tuple[int, str]]:
        results = []
        check = self.__input + added
        for index, item in enumerate(self.__items):
            text = item[0]
            if text.startswith(check):
                results.append((index, text))
        return results

    def __render_input(self):
        self._window.move(0, 0)
        available = self.size[1]
        portion = self.__input[:available]
        try:
            self._window.addnstr(portion, available)
            available -= len(portion)
        except curses.error:
            pass

        if self.__predicted is not None:
            displayed = len(portion)
            disp = self.__predicted[1][displayed:displayed+available]
            if disp:
                try:
                    self._window.addnstr(disp, available, curses.A_DIM)
                except curses.error:
                    pass
                self._window.move(0, min(len(portion) - 1, self.size[1] - 1))

    def __render_selected(self):
        if self.__selected == -1:
            self._window.move(0, 0)
            message = self.__placeholder or "No Selection"
            try:
                self._window.addnstr(message, self.size[1], curses.A_ITALIC)
            except curses.error:
                pass
            return

        text = self.__items[self.__selected][0]
        try:
            self._window.addnstr(text, self.size[1])
        except curses.error:
            pass

    def render(self):
        if self.focused:
            self.__render_input()
        else:
            self.__render_selected()

