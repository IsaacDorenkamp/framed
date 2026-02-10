import curses

from .widget import Widget

from .. import _log


class Label(Widget):
    _text: str
    def __init__(self, text: str):
        super().__init__()
        self._text = text

    def render(self):
        window = self._window
        window.move(0, 0)
        try:
            window.addnstr(self._text, self.size[1])
        except curses.error:
            pass

