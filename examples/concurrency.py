import asyncio
import random
import typing

import framed
from framed import keys
from framed.widgets import *
import framed.task


async def basic_task():
    await asyncio.sleep(random.randint(1, 5))


class DisplayPanel(framed.Panel):
    def __init__(self, region: framed.rect2, owner: framed.Manager, root: framed.App):
        super().__init__(region, owner, root)
        self.text = Editor()
        self.text.editable = False
        self.add(self.text)

    def arrange(self):
        fixed = self.fixed()
        fixed.add(self.text, 0, 0, 1000, 1000)


class ConcurrencyApp(framed.App):
    display: DisplayPanel

    def __init__(self, stdscr):
        super().__init__(stdscr)
        stack = self.stack()
        self.display = self.new_panel(DisplayPanel)
        stack.set_active_panel(0)
        self.set_control_handler(self.on_input)
        self.set_task_callback(self.on_task_complete)

    def on_input(self, ch: int):
        if ch == keys.PLUS:
            task_id = self.task(basic_task)
            self.display.text.append(f"Starting new task with id {task_id}\n")

    def on_task_complete(self, task_id: int, status: framed.task.TaskStatus, extra: typing.Any):
        if status == framed.task.TaskStatus.success:
            self.display.text.append(f"Task {task_id} completed.\n")
        elif status == framed.task.TaskStatus.failure:
            self.display.text.append(f"Task {task_id} failed: {str(extra)}\n")


def main(stdscr):
    import framed.palette
    framed.palette.setup()
    app = ConcurrencyApp(stdscr)
    app.run()


if __name__ == '__main__':
    import curses
    import logging
    logging.basicConfig(format="[%(levelname)s %(name)s] %(message)s", level=logging.DEBUG, handlers=[logging.FileHandler("/tmp/pylog", mode="w")])
    curses.wrapper(main)

