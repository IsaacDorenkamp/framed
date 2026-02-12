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
    manager = app.stack()

    first = app.new_panel(TestPanel)
    first.set_label_text("First Page")

    second = app.new_panel(TestPanel)
    second.set_label_text("Second Page")

    manager.set_active_panel(0)

    def handle_input(ch: int):
        if ch == curses.KEY_F1:
            manager.set_active_panel(0)
        elif ch == curses.KEY_F2:
            manager.set_active_panel(1)
        elif ch == curses.KEY_F3:
            first.set_label_text("Something else")
        elif ch == curses.KEY_F4:
            second.set_label_text("Something else 2")
        elif ch == 3:
            app.quit()

    app.set_control_handler(handle_input)

    app.run()


if __name__ == '__main__':
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    curses.wrapper(main)


