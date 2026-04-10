import curses

import framed
from framed.app import FocusCapture
from framed.const import HAlign
import framed.event
import framed.keys as keys
import framed.manager
import framed.palette
import framed.widgets


class TablePanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager, root: framed.App):
        super().__init__(region, owner, root)
        self.table = framed.widgets.Table(framed.widgets.TableTextModel)
        self.table.set_rows(100)
        self.table.set_columns(3)
        for row in range(100):
            for col in range(3):
                self.table.set_cell_text((row, col), f"row {row + 1}, col {col + 1}")
        self.add(self.table)

    def arrange(self):
        layout = self.fixed()
        layout.add(self.table, 0, 0, 1000, 1000)

    def sel_right(self):
        if self.table.selection is None:
            self.table.set_selection((0, 0))
        else:
            selection = self.table.selection
            self.table.set_selection((selection[0], (selection[1] + 1) % self.table.columns))

    def sel_left(self):
        if self.table.selection is None:
            self.table.set_selection((0, 0))
        else:
            selection = self.table.selection
            self.table.set_selection((selection[0], (selection[1] - 1) % self.table.columns))

    def sel_down(self):
        if self.table.selection is None:
            self.table.set_selection((0, 0))
        else:
            selection = self.table.selection
            self.table.set_selection(((selection[0] + 1) % self.table.rows, selection[1]))

    def sel_up(self):
        if self.table.selection is None:
            self.table.set_selection((0, 0))
        else:
            selection = self.table.selection
            self.table.set_selection(((selection[0] - 1) % self.table.rows, selection[1]))


class TableApp(framed.App):
    panel: TablePanel

    def __init__(self, stdscr):
        super().__init__(stdscr)
        self.manager = self.multiplex()
        self.panel = self.new_panel(TablePanel, split_path=())
        self.set_control_handler(self.on_input)

    def on_input(self, ch: int):
        if ch == keys.RIGHT:
            self.panel.sel_right()
        elif ch == keys.LEFT:
            self.panel.sel_left()
        elif ch == keys.UP:
            self.panel.sel_up()
        elif ch == keys.DOWN:
            self.panel.sel_down()


def main(stdscr):
    framed.palette.setup()
    app = TableApp(stdscr)
    app.run()


if __name__ == '__main__':
    import logging
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    curses.wrapper(main)

