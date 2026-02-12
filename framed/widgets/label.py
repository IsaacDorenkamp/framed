import curses

from .widget import Widget, invalidate


class Label(Widget):
    _text: str
    def __init__(self, text: str):
        super().__init__()
        self._text = text

    @invalidate
    def set_text(self, text) -> bool:
        if text != self._text:
            self._text = text
            return True

        return False

    def render(self):
        window = self._window
        window.move(0, 0)
        try:
            window.addnstr(self._text, self.size[1])
        except curses.error:
            pass

