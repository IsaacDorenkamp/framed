import curses

from ..const import HAlign
from .widget import Widget, invalidator


class Label(Widget):
    _text: str
    _bold: bool
    _italic: bool
    _underline: bool
    _align: HAlign

    def __init__(self, text: str, align: HAlign = HAlign.LEFT):
        super().__init__()
        self._text = text
        self._bold = False
        self._italic = False
        self._underline = False
        self._align = align

    @invalidator
    def set_text(self, text) -> bool:
        if text != self._text:
            self._text = text
            return True

        return False

    def get_text(self) -> str:
        return self._text

    @property
    def bold(self) -> bool:
        return self._bold

    @bold.setter
    def bold(self, bold: bool):
        self._bold = bold
        self.invalidate()

    @property
    def italic(self) -> bool:
        return self._italic

    @italic.setter
    def italic(self, italic: bool):
        self._italic = italic
        self.invalidate()

    @property
    def underline(self) -> bool:
        return self._underline

    @underline.setter
    def underline(self, underline: bool):
        self._underline = underline
        self.invalidate()

    @property
    def align(self) -> HAlign:
        return self._align

    @align.setter
    def align(self, align: HAlign):
        self._align = align
        self.invalidate()

    def render(self):
        window = self._window
        attr = (curses.A_BOLD if self.bold else 0) | (curses.A_UNDERLINE if self.underline else 0) | (curses.A_ITALIC if self.italic else 0)
        remaining_space = max(0, self.size[1] - len(self._text))
        offset = self._align.get_offset(remaining_space)
        available = self.size[1] - offset
        window.move(0, offset)
        try:
            window.addnstr(self._text, available, attr)
        except curses.error:
            pass

