import curses
import logging

import framed
import framed.palette
import framed.widgets


class TestPanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.label = framed.widgets.Label("Label")
        self.add(self.label)

    def set_label_text(self, text: str):
        self.label.set_text(text)

    def arrange(self):
        fixed = self.fixed()
        fixed.add(self.label, 0, 0, 1, 40)


def main(stdscr: curses.window):
    framed.palette.setup()
    app = framed.App(stdscr)
    manager = app.multiplex()
    split_a, split_b, split_c = manager.split(3)
    split2 = manager.split(2, split_b, direction=framed.Direction.vertical)
    manager.set_split_proportions((), (0.25, 0.25, 0.5))
    app.run()


if __name__ == '__main__':
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    curses.wrapper(main)

