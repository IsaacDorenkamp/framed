import curses
import logging

import framed
import framed.palette
import framed.widgets


class TestPanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.labels = []
        for i in range(9):
            label = framed.widgets.Label(f"Label {i + 1}")
            self.labels.append(label)
            self.add(label)

    def arrange(self):
        grid = self.grid()
        for index, label in enumerate(self.labels):
            grid.add(label, index // 3, index % 3)


def main(stdscr: curses.window):
    framed.palette.setup()
    app = framed.App(stdscr)
    manager = app.multiplex()
    split = manager.split(3)
    split2 = manager.split(4, split[1], direction=framed.Direction.vertical)
    manager.split(3, split2[3], direction=framed.Direction.horizontal)
    app.new_panel(TestPanel, split_path=split2[1])
    app.run()


if __name__ == '__main__':
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    logging.info("Alive!")
    curses.wrapper(main)


