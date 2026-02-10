import curses
import framed
import framed.widgets


class TestPanel(framed.Panel):
    def __init__(self, region: framed.rect2):
        super().__init__(region)
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
    app = framed.Framed(stdscr)
    manager = app.stack()
    app.new_panel(TestPanel)
    manager.set_active_panel(0)
    app.run()


if __name__ == '__main__':
    import logging
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    logging.info("Alive!")
    curses.wrapper(main)


