from abc import ABCMeta, abstractmethod
import curses
from dataclasses import dataclass
import enum

from .panel import FreePanel, Panel
from .struct import vec2, rect2
from ._tree import _node, _tree, TreeError
from . import _log
from . import util


class ManagerError(Exception):
    pass


FLAG_CHECK_FOCUS = 1


class Manager(metaclass=ABCMeta):
    """
    Similar in function to a Layout, a Manager is
    responsible for arranging Panels. Whereas a
    Layout arranges Widgets within a Panel, the
    Manager is responsible for positioning, sizing,
    and determining the visibility of Panels at
    the top level. While it seems like a Manager is
    oddly similar to a Layout, the internal logic is
    quite different. A Layout creates subwindows and
    assigns them to widgets, re-creating subwindows
    as necessary when a Panel changes. Since Panel
    instances have a persistent reference to a curses
    window, the Manager does not approach arrangement
    logic in the same manner. Instead, the Manager
    simply manipulates existing windows.
    """

    _stdscr: curses.window
    _size: vec2
    _free_panels: list[FreePanel]
    _flags: int

    def __init__(self, stdscr: curses.window):
        self._stdscr = stdscr
        self._size = vec2(*stdscr.getmaxyx())
        self._free_panels = []
        self._flags = 0

    def add_free_panel(self, panel: FreePanel):
        self._free_panels.append(panel)
        panel.render()
        self._stdscr.refresh()

    def remove_free_panel(self, panel: FreePanel):
        self._free_panels.remove(panel)
        panel._orphan()
        self.blit()
        self._flags |= FLAG_CHECK_FOCUS

    def set_screen_size(self, size: vec2):
        self._size = size
        self.arrange(size)
        self.__adjust_free_panels(size)

    def __adjust_free_panels(self, size: vec2):
        for panel in self._free_panels:
            # allow panel to reposition itself
            panel.reposition(size)

            # if the panel doesn't manage to bring itself
            # into the boundaries, force it
            far_y = panel.position.y + panel.size.y
            far_x = panel.position.x + panel.size.x
            if far_y >= size.y or far_x >= size.x:
                diff_y = max(0, far_y - size.y)
                diff_x = max(0, far_x - size.x)
                panel.set_position(vec2(
                    max(0, panel.position.y - diff_y),
                    max(0, panel.position.x - diff_x)
                ))

            new_y, new_x = panel.size
            if new_y > size.y:
                new_y = size.y

            if new_x > size.x:
                new_x = size.x

            panel.set_size(vec2(new_y, new_x))

    def get_centered_region(self, h: int, w: int) -> rect2:
        size = vec2(h, w)
        if size.y > self._size.y or size.x > self._size.x:
            raise ValueError(f"size '{size}' exceeds screen size in at least one dimension")

        diff = self._size.y - size.y, self._size.x - size.x
        return rect2(y=diff[0] // 2, x=diff[1] // 2, h=size.y, w=size.x)

    def check_flags(self) -> int:
        result = self._flags
        self._flags = 0
        return result

    @abstractmethod
    def add_panel(self, panel: Panel, *args, **kwargs):
        """
        Add a panel to the manager. Additional arguments
        may be needed per-implementation, which can be
        used to persistently store information about how
        the panels should be arranged.
        """
        raise NotImplementedError()

    @abstractmethod
    def arrange(self, size: vec2):
        """
        Arrange the available panels within a screen
        with the specified size.
        """
        raise NotImplementedError()

    @abstractmethod
    def show(self):
        """
        Render all the panels that should be visible.
        """
        raise NotImplementedError()

    def refresh(self):
        self._stdscr.clear()
        self.decorate()
        self._stdscr.noutrefresh()
        self.show()
        for panel in self._free_panels:
            panel.render()
        self._stdscr.noutrefresh()
        curses.doupdate()

    @abstractmethod
    def decorate(self):
        """
        Perform additional rendering tasks, such as drawing
        borders to visually separate panels.
        """
        raise NotImplementedError()

    @abstractmethod
    def request_update(self, panel: Panel) -> bool:
        """
        Determines whether a panel may perform updates to
        the screen. If a panel is not visible, it should not
        be able to perform updates to the screen, so this
        should return False in that case. If a panel is
        visible, however, this method should return True to
        permit the panel to perform a visual update.
        """
        raise NotImplementedError()

    @abstractmethod
    def blit(self):
        """
        Refresh all of the managed (not free) panels. Used to
        replace things which have been drawn-over by free panels.
        """
        raise NotImplementedError()


class StackManager(Manager):
    __panels: list[Panel]
    __active: int
    __showing: bool

    def __init__(self, stdscr: curses.window):
        super().__init__(stdscr)
        self.__panels = []
        self.__active = -1
        self.__showing = False

    # --- Manager method implementations ---
    def add_panel(self, panel: Panel):
        if panel in self.__panels:
            raise ManagerError("Cannot add panel to manager twice!")

        self.__panels.append(panel)

    def arrange(self, size: vec2):
        for panel in self.__panels:
            panel.set_size(size)

    def show(self):
        self.__showing = True
        self.__display()

    def __display(self):
        if self.__active == -1:
            return

        active_panel = self.__panels[self.__active]
        active_panel.render()

    def decorate(self):
        pass

    def request_update(self, panel: Panel) -> bool:
        if self.__active == -1:
            return False

        return panel == self.__panels[self.__active]

    def blit(self):
        for panel in self.__panels:
            panel.blit()

    # --- StackManager-specific methods ---
    def set_active_panel(self, active_index: int):
        if active_index >= len(self.__panels):
            raise ManagerError("active_index must be a valid index!")
        self.__active = active_index
        if self.__showing:
            self.__display()
            self.refresh()


class Direction(enum.IntEnum):
    horizontal = 0
    vertical = 1


@dataclass
class Split:
    portion: int
    panel_index: int
    region: rect2
    direction: Direction


class MultiplexManager(Manager):
    __splits: _tree[Split]  # scalars representing the portion of the screen which a split occupies
    __panels: list[Panel]
    __visible: list[Panel]

    def __init__(self, stdscr: curses.window, top_level_split_direction: Direction = Direction.horizontal):
        super().__init__(stdscr)
        self.__splits = _tree(Split(0, -1, rect2(0, 0, 0, 0), top_level_split_direction))
        self.__panels = []
        self.__visible = []

    # --- Manager method implementations ---
    def add_panel(self, panel: Panel, split_path: tuple[int, ...]):
        self.__panels.append(panel)
        try:
            split = self.__splits.get_node(split_path)
            if split.children:
                raise ManagerError("Split '%s' is not a bottom-level split!" % str(split_path))
            split.value.panel_index = len(self.__panels) - 1
        except TreeError:
            raise ManagerError("No split with path '%s'" % str(split_path))

    def arrange(self, size: vec2):
        base_region = rect2(0, 0, size.y, size.x)
        self.__visible.clear()
        self.__arrange_split(self.__splits.root, base_region)

    def __arrange_split(self, split_node: _node[Split], region: rect2):
        split = split_node.value
        total_directional_space = region.w if split.direction == Direction.horizontal else region.h
        directional_space = total_directional_space - (len(split_node.children) - 1)
        weights = [child.value.portion for child in split_node.children]
        sizes = util.distribute(directional_space, weights)
        if any(x == 0 for x in sizes):
            return

        consumed_space = 0
        for index, child_node in enumerate(split_node.children):
            child = child_node.value
            if split.direction == Direction.horizontal:
                new_region = rect2(region.y, region.x + consumed_space, region.h, sizes[index])
            else:
                new_region = rect2(region.y + consumed_space, region.x, sizes[index], region.w)

            child.region = new_region
            if child.panel_index != -1:
                panel = self.__panels[child.panel_index]
                panel.set_size(vec2(child.region.h, child.region.w))
                panel.set_position(vec2(child.region.y, child.region.x))
                self.__visible.append(panel)

            consumed_space += sizes[index] + 1  # add one for border
            
            if child_node.children:
                self.__arrange_split(child_node, child.region)

    def show(self):
        for panel in self.__visible:
            panel.render()

    def decorate(self):
        root = self.__splits.root
        self.__decorate(root)

    def __decorate(self, split_node: _node[Split]):
        split = split_node.value
        for index, child_node in enumerate(split_node.children):
            child = child_node.value
            _log.info(f"region: {child.region}")
            if index > 0:
                # draw border
                if split.direction == Direction.horizontal:
                    for y in range(child.region.h):
                        self._stdscr.move(child.region.y + y, child.region.x - 1)
                        self._stdscr.addch("\u2502")
                else:
                    self._stdscr.move(child.region.y - 1, child.region.x)
                    self._stdscr.addnstr("\u2500" * child.region.w, child.region.w)

        self._stdscr.noutrefresh()

        for child_node in split_node.children:
            child = child_node.value
            self.__decorate(child_node)
            self.__connect_borders(child.region, split.direction)

    def __update_char(self, y: int, x: int, replace_map: dict[int, int]):
        existing_raw = self._stdscr.inch(y, x)
        if existing_raw == 0xffffffff:
            return

        existing = existing_raw & 0xffff
        updated = replace_map.get(existing)
        if updated is not None:
            self._stdscr.move(y, x)
            self._stdscr.addch(chr(updated), curses.A_DIM)

    def __connect_borders(self, region: rect2, parent_direction: Direction):
        # TODO: Support non-unicode systems
        max_y, max_x = self._stdscr.getmaxyx()
        if parent_direction == Direction.horizontal:
            y, x = region.y - 1, region.x - 1
            if y >= 0:
                self.__update_char(y, x, { 0x2534: 0x253C, 0x2500: 0x252C })

            y = region.y + region.h  # 1 below the bottom
            if y < max_y:
                self.__update_char(y, x, { 0x252C: 0x253C, 0x2500: 0x2534 })
        else:
            y, x = region.y - 1, region.x - 1
            if x >= 0:
                self.__update_char(y, x, { 0x2524: 0x253C, 0x2502: 0x251C })

            x = region.x + region.w
            if x < max_x:
                self.__update_char(y, x, { 0x251C: 0x253C, 0x2502: 0x2524 })

    def __disconnect_borders(self, region: rect2, parent_direction: Direction):
        max_y, max_x = self._stdscr.getmaxyx()
        if parent_direction == Direction.horizontal:
            y, x = region.y - 1, region.x - 1
            if y >= 0:
                self.__update_char(y, x, { 0x253C: 0x2534, 0x252C: 0x2500 })

            y = region.y + region.h
            if y < max_y:
                self.__update_char(y, x, { 0x253C: 0x252C, 0x2534: 0x2500 })
        else:
            y, x = region.y - 1, region.x - 1
            if x >= 0:
                self.__update_char(y, x, { 0x253C: 0x2524, 0x251C: 0x2502 })

            x = region.x + region.w
            if x < max_x:
                self.__update_char(y, x, { 0x253C: 0x251C, 0x2524: 0x2502 })

    def request_update(self, panel: Panel) -> bool:
        return panel in self.__visible

    def blit(self):
        for panel in self.__panels:
            panel.blit()

    # --- MultiplexManager-specific methods ---
    def split(self, parts: int, path: tuple[int, ...] | None = None, direction: Direction = Direction.horizontal) -> list[tuple[int, ...]]:
        if path is None:
            path = ()

        node = self.__splits.get_node(path)
        if node.children:
            raise ManagerError("'%s' is not a bottom-level split!" % str(path))
        node.value.direction = direction
        splits = []
        for _ in range(parts):
            splits.append(self.__splits.insert(path, Split(1, -1, rect2(), direction)))
        return splits

    def set_proportions(self, path: tuple[int, ...], proportions: tuple[int, ...]):
        node = self.__splits.get_node(path)
        if not node.children:
            raise ManagerError("'%s' is a bottom-level split!" % str(path))

        if len(node.children) != len(proportions):
            raise ManagerError("Needed %d proportions, got %d instead" % (len(node.children), len(proportions)))

        for child, portion in zip(node.children, proportions):
            child.value.portion = portion

