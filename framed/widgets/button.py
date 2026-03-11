import curses
import enum

from .. import keys
from .. import palette
from ..struct import vec2
from ..event import ActionEvent
from .widget import FocusHolder


class ButtonAction(enum.Enum):
    command_press = "command_press"
    command_blur = "command_blur"


class Button(FocusHolder):
    _DEFAULT_BINDINGS = {
        keys.ENTER: ButtonAction.command_press,
        keys.ESCAPE: ButtonAction.command_blur,
    }

    __text: str
    __bordered: bool
    __bindings: dict[int, ButtonAction]
    __focus_attr: int
    __focus_fg: str

    def __init__(self, text: str, bordered: bool = True):
        super().__init__(greedy=False, enabled_events=[ActionEvent.tag])
        self.__text = text
        self.__bordered = bordered
        self.__focus_attr = 0
        self.__focus_fg = "default"
        self.__bindings = Button._DEFAULT_BINDINGS.copy()

    # --- Widget Implementation ---
    def on_focus(self):
        self.invalidate()

    def on_unfocus(self):
        self.invalidate()

    def on_input(self, ch: int):
        action = self.__bindings.get(ch)
        if action is not None:
            match action:
                case ButtonAction.command_press:
                    self._emit(ActionEvent(self))
            self._relinquish()
            return True

        return False

    def render(self):
        focus_color = palette.color_pair(self.__focus_fg, "default")
        if self.__bordered:
            if self._focused:
                self._window.attron(focus_color)
            self._window.box()
            if self._focused:
                self._window.attroff(focus_color)
            offset = (1, 1)
            width = max(0, self.size[1] - 2)
            if (
                offset[0] >= self.size[0] or
                offset[1] >= width - 1
            ):
                # button is too small to render
                return
        else:
            offset = (0, 0)
            width = self.size[1]

        self._window.move(*offset)
        try:
            self._window.addnstr(self.__text, width, (self.__focus_attr | palette.color_pair(self.__focus_fg, "default")) if self.focused else 0)
        except curses.error:
            pass

    @property
    def min_size(self):
        return vec2(3, len(self.__text) + 2) if self.__bordered else vec2(1, len(self.__text))

    # --- Bindings ---
    def bind(self, key: int, action: ButtonAction):
        self.__bindings[key] = action

    def unbind(self, key: int = -1, action: ButtonAction | None = None):
        if key == -1 and action is None:
            raise ValueError("Must provide either a key code or an action.")
        elif key != -1 and action is not None:
            raise ValueError("Must provide either a key code or an action, not both.")

        if key != -1:
            if key in self.__bindings:
                del self.__bindings[key]
        else:
            keys = list(self.__bindings.keys())
            for key in keys:
                if self.__bindings[key] == action:
                    del self.__bindings[key]

    def unbind_all(self):
        self.__bindings.clear()

    # --- Appearance ---
    @property
    def bordered(self) -> bool:
        return self.__bordered

    @bordered.setter
    def bordered(self, bordered: bool):
        if bordered != self.__bordered:
            self.__bordered = bordered
            self.invalidate()

    @property
    def focus_underline(self) -> bool:
        return self.__focus_attr & curses.A_UNDERLINE == curses.A_UNDERLINE

    @focus_underline.setter
    def focus_underline(self, underline: bool):
        if underline:
            self.__focus_attr |= curses.A_UNDERLINE
        else:
            self.__focus_attr &= ~curses.A_UNDERLINE
        
        if self._focused:
            self.invalidate()

    @property
    def focus_bold(self) -> bool:
        return self.__focus_attr & curses.A_BOLD == curses.A_BOLD

    @focus_bold.setter
    def focus_bold(self, bold: bool):
        if bold:
            self.__focus_attr |= curses.A_BOLD
        else:
            self.__focus_attr &= ~curses.A_BOLD

        if self._focused:
            self.invalidate()

    @property
    def focus_italic(self) -> bool:
        return self.__focus_attr & curses.A_ITALIC == curses.A_ITALIC

    @focus_italic.setter
    def focus_italic(self, italic: bool):
        if italic:
            self.__focus_attr |= curses.A_ITALIC
        else:
            self.__focus_attr &= ~curses.A_ITALIC

        if self._focused:
            self.invalidate()

    @property
    def focus_foreground(self):
        return self.__focus_fg

    @focus_foreground.setter
    def focus_foreground(self, foreground: str):
        self.__focus_fg = foreground
        if self._focused:
            self.invalidate()

