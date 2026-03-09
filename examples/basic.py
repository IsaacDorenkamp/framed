import curses
import logging

import framed
import framed.event
import framed.keys
import framed.palette
import framed.widgets


class ListBoxPanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.box = framed.widgets.ListBox()
        self.box.bind(framed.keys.j, framed.widgets.ListBoxAction.nav_down)
        self.box.bind(framed.keys.k, framed.widgets.ListBoxAction.nav_up)
        self.box.page = 20
        self.add(self.box)
        for i in range(150):
            self.box.add_item("A" * (i + 1), data=i)

    def arrange(self):
        layout = self.fixed()
        layout.add(self.box, 0, 0, 1000, 1000)


class ReportPanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.editor = framed.widgets.Editor()
        self.add(self.editor)

    def arrange(self):
        layout = self.fixed()
        layout.add(self.editor, 0, 0, 1000, 1000)

    def accept_report(self, event: framed.event.ChangeEvent[framed.widgets.ListBoxChange]):
        self.editor.append(f"Selected {event.value.label} (index {event.value.index})\n")


def main(stdscr: curses.window):
    framed.palette.setup()
    app = framed.App(stdscr)
    manager = app.multiplex()

    list_split, report_split = manager.split(2, direction=framed.Direction.vertical)
    manager.set_proportions(path=(), proportions=(3, 1))
    list_panel = app.new_panel(ListBoxPanel, split_path=list_split)
    report_panel = app.new_panel(ReportPanel, split_path=report_split)

    list_panel.box.listen(framed.event.ChangeEvent, report_panel.accept_report)

    def handle_input(ch: int):
        if ch == 3:
            app.quit()
        elif ch == framed.keys.l:
            app.focus(list_panel.box)
        elif ch == framed.keys.L:
            list_panel.box.set_selection(0)
        elif ch == framed.keys.DELETE:
            index = list_panel.box.get_selection_index()
            if index >= 0:
                item_text = list_panel.box.get_item_text(index)
                list_panel.box.remove_item(index)
                report_panel.editor.append(f"Removed list item {item_text} (index {index})\n")
        else:
            return framed.FocusCapture.passthrough

        return framed.FocusCapture.capture

    app.set_control_handler(handle_input)

    app.run()


if __name__ == '__main__':
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    curses.wrapper(main)

