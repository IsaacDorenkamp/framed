import curses
import logging
import random

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
        self.editor.editable = False
        self.add(self.editor)

    def arrange(self):
        layout = self.fixed()
        layout.add(self.editor, 0, 0, 1000, 1000)

    def accept_report(self, event: framed.event.ChangeEvent[framed.widgets.ListBoxChange]):
        self.editor.append(f"Selected {event.value.label} (index {event.value.index})\n")


class MiscPanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.box = framed.widgets.OptionBox()
        self.box.add_option("Option A", value="Option A")
        self.box.add_option("Option B", value="Option B")
        self.box.add_option("Something Else", value="Something Else")
        self.box.default = "Something Else"
        self.box.listen(framed.event.ChangeEvent, self.on_change)
        self.add(self.box)

    def arrange(self):
        layout = self.fixed()
        layout.add(self.box, 2, 5, 1, 5)

    def on_change(self, event: framed.event.ChangeEvent):
        colors = list(framed.palette.get_color_names())
        new_color = random.choice(colors)
        self.box.foreground = new_color


def main(stdscr: curses.window):
    framed.palette.setup()
    app = framed.App(stdscr)
    manager = app.multiplex()

    listbox_split, misc_split = manager.split(2, direction=framed.Direction.horizontal)
    list_split, report_split = manager.split(2, listbox_split, direction=framed.Direction.vertical)
    manager.set_proportions(path=(), proportions=(1, 2))
    manager.set_proportions(path=listbox_split, proportions=(3, 1))
    list_panel = app.new_panel(ListBoxPanel, split_path=list_split)
    report_panel = app.new_panel(ReportPanel, split_path=report_split)

    list_panel.box.listen(framed.event.ChangeEvent, report_panel.accept_report)

    misc_panel = app.new_panel(MiscPanel, split_path=misc_split)

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
        elif ch == framed.keys.PLUS:
            index = list_panel.box.get_selection_index()
            if index >= 0:
                list_panel.box.insert_item(index, "New Item")
                report_panel.editor.append(f"Inserted item at index {index}\n")
        elif ch == framed.keys.R:
            app.focus(report_panel.editor)
        elif ch == framed.keys.B:
            app.focus(misc_panel.box)
        else:
            return framed.FocusCapture.passthrough

        return framed.FocusCapture.capture

    app.set_control_handler(handle_input)

    app.run()


if __name__ == '__main__':
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    curses.wrapper(main)

