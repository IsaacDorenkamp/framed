import curses
from dataclasses import dataclass
import enum
import typing

from .. import keys
from ..event.change import ChangeEvent
from .widget import CursorMode, FocusHolder


T = typing.TypeVar("T")


@dataclass(frozen=True)
class ListBoxChange(typing.Generic[T]):
    label: str
    index: int
    value: T | None


class ListBoxAction(enum.Enum):
    nav_up = "nav_up"
    nav_down = "nav_down"
    nav_page_up = "nav_page_up"
    nav_page_down = "nav_page_down"

    select = "select"
    cancel = "cancel"


class ListBox(FocusHolder, typing.Generic[T]):
    _DEFAULT_BINDINGS = {
        keys.UP: ListBoxAction.nav_up,
        keys.DOWN: ListBoxAction.nav_down,
        keys.PGDN: ListBoxAction.nav_page_down,
        keys.PGUP: ListBoxAction.nav_page_up,
        keys.ENTER: ListBoxAction.select,
        keys.ESCAPE: ListBoxAction.cancel,
    }

    __items: list[tuple[str, T | None]]
    __selection: int
    __cursor: int
    __scroll: int
    __page: int
    __bindings: dict[int, ListBoxAction]

    def __init__(self):
        super().__init__(enabled_events=[ChangeEvent.tag])
        self.__items = []
        self.__selection = -1
        self.__cursor = -1
        self.__scroll = 0
        self.__page = -1
        self.__bindings = ListBox._DEFAULT_BINDINGS.copy()

    def on_focus(self):
        self.cursor(CursorMode.hidden)
        self.__cursor = max(0, self.__selection)
        self.__render_row(self.__cursor)
        self._window.refresh()

    def on_unfocus(self):
        prev_cursor = self.__cursor
        self.__cursor = -1
        self.__render_row(prev_cursor)
        self._window.refresh()

    def on_input(self, ch: int):
        action = self.__bindings.get(ch)
        if action is None:
            return False

        dirty = True
        match action:
            case ListBoxAction.nav_down:
                if self.__cursor < len(self.__items) - 1:
                    self.__cursor += 1
                    self.__quick_adjust_scroll()
                    self.__render_row(self.__cursor - 1)
                    self.__render_row(self.__cursor)
                else:
                    dirty = False
            case ListBoxAction.nav_up:
                if self.__cursor > 0:
                    self.__cursor -= 1
                    self.__quick_adjust_scroll()
                    self.__render_row(self.__cursor)
                    self.__render_row(self.__cursor + 1)
                else:
                    dirty = False
            case ListBoxAction.nav_page_down:
                self.__pageturn(1)
            case ListBoxAction.nav_page_up:
                self.__pageturn(-1)
            case ListBoxAction.select:
                previous = self.__selection
                self.__selection = self.__cursor
                self.__render_row(previous)
                self.__render_row(self.__selection)
                selection = self.__items[self.__selection]
                self._emit(ChangeEvent[ListBoxChange[T]](self, ListBoxChange[T](selection[0], self.__selection, selection[1])))
                self._relinquish()
            case ListBoxAction.cancel:
                self._relinquish()
                self.__adjust_scroll()

        if dirty:
            self._window.refresh()

        return True

    def __pageturn(self, direction: int):
        if self.__page == -1:
            page_size = self.size[0]
        else:
            page_size = self.__page

        amount = direction * page_size
        prev = self.__cursor
        self.__cursor = max(0, min(len(self.__items) - 1, self.__cursor + amount))
        invalidated = self.__adjust_scroll()
        if not invalidated:
            self.__render_row(prev)
            self.__render_row(self.__cursor)

    def __adjust_scroll(self):
        invalidate = True
        if self.focused:
            # when focused, always ensure that the cursor is visible
            if self.__cursor >= self.__scroll + self.size[0]:
                self.__scroll = self.__cursor - self.size[0] + 1
            elif self.__cursor < self.__scroll:
                self.__scroll = self.__cursor
            else:
                invalidate = False
        else:
            # if not focused, always ensure the selection is visible
            if self.__selection >= self.__scroll + self.size[0]:
                self.__scroll = self.__selection - self.size[0] + 1
            elif self.__selection < self.__scroll:
                self.__scroll = self.__selection
            else:
                invalidate = False
        if invalidate:
            self.invalidate()
        return invalidate

    def __quick_adjust_scroll(self):
        # a variant of adjust scroll which leverages scroll() when possible,
        # which avoids total re-renders
        if self.__cursor >= self.__scroll + self.size[0]:
            self.scrollok = True
            self._window.scroll(1)
            self.scrollok = False
            self.__scroll += 1
        elif self.__cursor < self.__scroll:
            self.scrollok = True
            self._window.scroll(-1)
            self.scrollok = False
            self.__scroll -= 1

    def __render_row(self, index: int):
        if (
            index < self.__scroll or
            index >= self.__scroll + self.size[0]
        ):
            return

        render_at = index - self.__scroll
        self._window.move(render_at, 0)
        if index >= len(self.__items):
            # index is in visual range, but no item exists there
            self._window.clrtoeol()
            return

        label = self.__items[index][0]
        highlighted = index in self.should_highlight
        try:
            line = label.ljust(self.size[1], " ")
            self._window.addnstr(line, self.size[1], self.highlight_attr if highlighted else 0)
        except curses.error:
            pass

    def render(self):
        for index in range(self.__scroll, min(self.__scroll + self.size[0], len(self.__items))):
            self.__render_row(index)

    @property
    def should_highlight(self) -> set[int]:
        return {self.__selection, self.__cursor}

    @property
    def highlight_attr(self):
        return curses.A_REVERSE | (curses.A_ITALIC if self.focused else 0)

    @property
    def page(self) -> int:
        return self.__page

    @page.setter
    def page(self, page: int):
        if page < -1 or page == 0:
            raise ValueError("page must be non-zero, and cannot be < -1")
        self.__page = page

    # --- Bindings ---
    def bind(self, key: int, action: ListBoxAction):
        self.__bindings[key] = action

    def unbind(self, key: int = -1, action: ListBoxAction | None = None):
        if key == -1 and action is None:
            raise ValueError("Must provide either a key or an action.")
        elif key != -1 and action is not None:
            raise ValueError("Must provide either a key or an action, not both.")

        if key != -1 and key in self.__bindings:
            del self.__bindings[key]
        elif action is not None:
            keys = list(self.__bindings.keys())
            for key in keys:
                if self.__bindings[key] == action:
                    del self.__bindings[key]

    # --- Items and Selection ---
    def add_item(self, label: str, data: T | None = None):
        self.__items.append((label, data))
        if self.request_update():
            self.__render_row(len(self.__items) - 1)

    def insert_item(self, index: int, label: str, data: T | None = None):
        if index < 0 or index > len(self.__items):
            raise ValueError(f"insert index out of range: {index}")

        self.__items.insert(index, (label, data))
        if self.request_update():
            end = min(len(self.__items) - 1, max(0, index - self.__scroll) + index + self.size[0])
            for row in range(index, end):
                self.__render_row(row)
            self._window.refresh()

    def remove_item(self, index: int):
        if index < 0 or index >= len(self.__items):
            raise ValueError(f"remove index must be between 0 and {len(self.__items) - 1}, inclusive")

        prev = self.__selection
        if self.__selection >= index:
            # If we remove an item at or before the selection, adjust the
            # selection index to compensate. If selection is 0, then it
            # will become -1, which is equivalent to "no selection."
            self.__selection -= 1

        prev_cursor = self.__cursor
        if self.__cursor >= index:
            self.__cursor -= 1

        can_update = self.request_update()
        if can_update:
            self.__render_row(prev_cursor)
            self.__render_row(prev)
            self.__render_row(self.__selection)
        self.__items.pop(index)
        if can_update:
            for i in range(index, index + self.size[0]):
                self.__render_row(i)
            self._window.refresh()

    def find_item_by_text(self, text: str) -> int:
        for index, item in enumerate(self.__items):
            if item[0] == text:
                return index

        return -1

    def find_item(self, value: T) -> int:
        for index, item in enumerate(self.__items):
            if item[1] == value:
                return index

        return -1

    def get_item_text(self, index: int) -> str:
        if index < 0 or index >= len(self.__items):
            raise ValueError(f"No item at index '{index}'")

        return self.__items[index][0]

    def get_item(self, index: int) -> T | None:
        if index < 0 or index >= len(self.__items):
            raise ValueError(f"No item at index '{index}'")

        return self.__items[index][1]

    def get_selection_index(self) -> int:
        return self.__selection

    def get_selection_text(self) -> str | None:
        if self.__selection == -1:
            return None
        return self.__items[self.__selection][0]

    def get_selection(self) -> T | None:
        if self.__selection == -1:
            return None
        return self.__items[self.__selection][1]

    def set_selection(self, index: int):
        if index == self.__selection:
            return

        previous = self.__selection
        if index == -1:
            self.__selection = -1
        elif index < len(self.__items):
            self.__selection = index

        if self.request_update():
            self.__adjust_scroll()
            self.__render_row(previous)
            self.__render_row(self.__selection)
            self._window.refresh()

