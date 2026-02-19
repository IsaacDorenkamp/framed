import curses

from .widget import Widget, invalidator


class Label(Widget):
    _text: str
    _bold: bool
    _italic: bool
    _underline: bool
    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self._bold = False
        self._italic = False
        self._underline = False

    @invalidator
    def set_text(self, text) -> bool:
        if text != self._text:
            self._text = text
            return True

        return False

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

    def render(self):
        window = self._window
        window.move(0, 0)
        try:
            attr = (curses.A_BOLD if self.bold else 0) | (curses.A_UNDERLINE if self.underline else 0) | (curses.A_ITALIC if self.italic else 0)
            window.addnstr(self._text, self.size[1], attr)
        except curses.error:
            pass

