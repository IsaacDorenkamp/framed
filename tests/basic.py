import curses
import logging
import random
import string

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

    def set_label_colors(self, foreground: str, background: str):
        self.label.foreground = foreground
        self.label.background = background

    def arrange(self):
        fixed = self.fixed()
        fixed.add(self.label, 0, 0, 1, 40)


def main(stdscr: curses.window):
    framed.palette.setup()
    app = framed.App(stdscr)
    manager = app.multiplex()

    title, content, status = manager.split(3, direction=framed.Direction.vertical)
    manager.set_proportions((), (0, 1, 0))

    title_panel = app.new_panel(TestPanel, split_path=title)
    content_panel = app.new_panel(TestPanel, split_path=content)
    status_panel = app.new_panel(TestPanel, split_path=status)

    title_panel.set_label_text("Title")
    title_panel.label.bold = True

    content_panel.set_label_text("Content")
    content_panel.label.italic = True
    content_panel.label.bold = True
    content_panel.label.underline = True

    status_panel.set_label_text("Status")
    status_panel.label.underline = True

    def handle_input(ch: int):
        if ch == 3:
            app.quit()
        elif ch == ord("c"):
            colors = list(framed.palette.get_color_names())
            foreground = random.choice(colors)
            colors.remove(foreground)
            background = random.choice(colors)

            for panel in (title_panel, content_panel, status_panel):
                panel.set_label_text("".join([random.choice(string.ascii_letters) for _ in range(25)]))
                panel.set_label_colors(foreground, background)

    app.set_control_handler(handle_input)

    app.run()


if __name__ == '__main__':
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    curses.wrapper(main)


