import curses

from framed.app import FocusCapture
from framed.const import HAlign
import framed.event
import framed.keys
import framed.manager
import framed.palette
import framed.widgets


class TitlePanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.title = framed.widgets.Label("Untitled")
        self.title.italic = True
        self.add(self.title)

    def set_title(self, title: str):
        self.title.italic = False
        self.title.set_text(title)

    def clear_title(self):
        self.title.italic = True
        self.title.set_text("Untitled")

    def get(self) -> str | None:
        if self.title.italic:
            return None
        else:
            return self.title.get_text()

    def arrange(self):
        layout = self.grid()
        layout.add(self.title, row=0, col=0)


class NotepadPanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.editor = framed.widgets.Editor()
        self.add(self.editor)

    def arrange(self):
        layout = self.grid()
        layout.add(self.editor, row=0, col=0)


class StatusPanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.status = framed.widgets.Label("Ready")
        self.status.foreground = "green"
        self.add(self.status)

    def arrange(self):
        layout = self.grid()
        layout.add(self.status, row=0, col=0)


class OpenDialog(framed.FreePanel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.bordered = True

        self.label = framed.widgets.Label("Open: ", align=HAlign.RIGHT)
        self.prompt = framed.widgets.Editor(model_cls=framed.widgets.LineTextModel)
        self.prompt.bind(framed.keys.ENTER, framed.widgets.EditorAction.edit_finish)
        self.prompt.unbind(framed.keys.ESCAPE)

        self.add(self.label)
        self.add(self.prompt)

    def arrange(self):
        layout = self.flex()
        layout.set_row_weight(0, 1)
        layout.set_row_weight(2, 1)
        layout.add(self.label, row=1, weight=1)
        layout.add(self.prompt, row=1, weight=3)

    def reposition(self, size: framed.vec2):
        new_size = framed.vec2(min(size.y, 5), min(size.x, 50))
        new_region = self._owner.get_centered_region(*new_size)
        self.set_position(framed.vec2(new_region.y, new_region.x))
        self.set_size(framed.vec2(new_region.h, new_region.w))


class SaveDialog(framed.FreePanel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.bordered = True

        self.label = framed.widgets.Label("Save: ", align=HAlign.RIGHT)
        self.prompt = framed.widgets.Editor(model_cls=framed.widgets.LineTextModel)
        self.prompt.bind(framed.keys.LF, framed.widgets.EditorAction.edit_finish)
        self.prompt.unbind(framed.keys.ESCAPE)

        self.add(self.label)
        self.add(self.prompt)

    def arrange(self):
        layout = self.flex()
        layout.set_row_weight(0, 1)
        layout.set_row_weight(2, 1)
        layout.add(self.label, row=1, weight=1)
        layout.add(self.prompt, row=1, weight=3)

    def reposition(self, size: framed.vec2):
        new_size = framed.vec2(min(size.y, 5), min(size.x, 50))
        new_region = self._owner.get_centered_region(*new_size)
        self.set_position(framed.vec2(new_region.y, new_region.x))
        self.set_size(framed.vec2(new_region.h, new_region.w))


class NotepadApp(framed.App):
    manager: framed.manager.MultiplexManager

    def __init__(self, stdscr):
        super().__init__(stdscr)
        self.manager = self.multiplex()
        title_split, notepad_split, status_split = self.manager.split(3, direction=framed.Direction.vertical)

        self.title = self.new_panel(TitlePanel, split_path=title_split)
        self.notepad = self.new_panel(NotepadPanel, split_path=notepad_split)
        self.status = self.new_panel(StatusPanel, split_path=status_split)

        self.manager.set_proportions((), (0, 1, 0))

        self.set_control_handler(self.on_input)

    def save(self, filename: str) -> bool:
        try:
            with open(filename, "w", encoding="ascii") as fp:
                fp.write(self.notepad.editor.get_text())
            self.status.status.foreground = "green"
            self.status.status.set_text(f"Saved to {filename}")
            return True
        except IOError as err:
            self.status.status.foreground = "red"
            self.status.status.set_text(f"Could not write to file: {err}")
            return False

    def on_input(self, ch: int):
        focus_cap = FocusCapture.capture
        if ch == ord('i'):
            self.focus(self.notepad.editor)
        elif ch == framed.keys.CTRL_O:
            self.dialog = self.new_free_panel(OpenDialog, region=self.get_centered_region(5, 50))
            self.dialog.prompt.listen(framed.event.ChangeEvent, self.on_open_file_change)
            self.focus(self.dialog.prompt)
        elif ch == framed.keys.CTRL_S:
            filename = self.title.get()
            if filename is not None:
                self.save(filename)
            else:
                self.dialog = self.new_free_panel(SaveDialog, region=self.get_centered_region(5, 50))
                self.dialog.prompt.listen(framed.event.ChangeEvent, self.on_save_file_change)
                self.focus(self.dialog.prompt)
        elif ch == framed.keys.CTRL_N:
            self.title.clear_title()
            self.notepad.editor.set_text("")
        elif ch == framed.keys.ESCAPE:
            self.close_dialog()
        else:
            focus_cap = FocusCapture.passthrough

        return focus_cap

    def close_dialog(self):
        dialog = getattr(self, "dialog", None)
        if dialog is not None:
            dialog.close()
            self.dialog = None

    def on_open_file_change(self, event: framed.event.ChangeEvent[str]):
        desired_file = event.value
        try:
            with open(desired_file, "r", encoding="ascii") as fp:
                content = fp.read()
            self.title.set_title(desired_file)
            self.notepad.editor.set_text(content)
            self.close_dialog()
        except IOError as err:
            self.status.status.foreground = "red"
            self.status.status.set_text(f"Could not open file: {err}")

    def on_save_file_change(self, event: framed.event.ChangeEvent[str]):
        desired_value = event.value
        self.close_dialog()
        if self.save(desired_value):
            self.title.set_title(desired_value)


def main(stdscr):
    curses.curs_set(0)
    framed.palette.setup()
    app = NotepadApp(stdscr)
    app.run()


if __name__ == '__main__':
    import logging
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    curses.wrapper(main)

