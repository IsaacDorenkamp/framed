import curses

from framed.app import FocusCapture
import framed.keys
import framed.manager
import framed.palette
import framed.widgets
import framed.widgets.text


class TitlePanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager):
        super().__init__(region, owner)
        self.title = framed.widgets.Editor(model_cls=framed.widgets.text.LineTextModel)
        self.title.bind(framed.keys.ENTER, framed.widgets.text.EditorAction.edit_finish)
        self.add(self.title)

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

    def save(self):
        filename = self.title.title.get_text()
        try:
            with open(filename, "w") as fp:
                fp.write(self.notepad.editor.get_text())
            self.status.status.foreground = "green"
            self.status.status.set_text(f"Saved to {filename}")
        except IOError as err:
            self.status.status.foreground = "red"
            self.status.status.set_text(f"Could not write to file: {err}")

    def on_input(self, ch: int):
        focus_cap = FocusCapture.capture
        if ch == ord('i'):
            self.focus(self.notepad.editor)
        elif ch == ord('r'):
            self.focus(self.title.title)
        elif ch == framed.keys.CTRL_S:
            self.save()
        else:
            focus_cap = FocusCapture.passthrough

        return focus_cap


def main(stdscr):
    curses.curs_set(0)
    framed.palette.setup()
    app = NotepadApp(stdscr)
    app.run()


if __name__ == '__main__':
    curses.wrapper(main)

