from abc import ABCMeta, abstractmethod
import curses
from dataclasses import dataclass
import enum
import math

from .panel import Panel
from .struct import vec2, rect2
from ._tree import _node, _tree, TreeError


class ManagerError(Exception):
    pass


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

    def __init__(self, stdscr: curses.window):
        self._stdscr = stdscr

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
        self._stdscr.noutrefresh()
        self.show()
        self.decorate()
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

    # --- StackManager-specific methods ---
    def set_active_panel(self, active_index: int):
        if active_index >= len(self.__panels):
            raise ManagerError("active_index must be a valid index!")
        self.__active = active_index
        if self.__showing:
            self.__display()


class Direction(enum.IntEnum):
    horizontal = 0
    vertical = 1


@dataclass
class Split:
    portion: float
    panel_index: int
    region: rect2
    direction: Direction


class MultiplexManager(Manager):
    __splits: _tree[Split]  # scalars representing the portion of the screen which a split occupies
    __panels: list[Panel]
    __visible: list[Panel]

    def __init__(self, top_level_split_direction: Direction = Direction.horizontal):
        self.__splits = _tree(Split(1.0, -1, rect2(0, 0, 0, 0), top_level_split_direction))
        self.__panels = []

    # --- Manager method implementations ---
    def add_panel(self, panel: Panel, split_path: tuple[int, ...]):
        self.__panels.append(panel)
        try:
            split = self.__splits.get(split_path)
            split.panel_index = len(self.__panels) - 1
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

        if directional_space < len(split_node.children):
            # there's not enough space to fit the children. in this case, we will simply stop arranging
            # and not include the panels in the list of visible panels.
            return

        used_space = 0
        sizes = [0] * len(split_node.children)
        for index, child in enumerate(split_node.children):
            child_space = max(1, math.floor(directional_space * child.value.portion))
            sizes[index] = child_space
            used_space += child_space

        distribute_index = 0
        while used_space < directional_space:
            sizes[distribute_index] += 1
            distribute_index = (distribute_index + 1) % len(sizes)

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
        # TODO: Draw borders!
        pass

    def request_update(self, panel: Panel) -> bool:
        return panel in self.__visible

    # --- MultiplexManager-specific methods ---
    def split(self, path: tuple[int, ...] | None = None, direction: Direction = Direction.horizontal) -> tuple[int, ...]:
        if path is None:
            path = ()

        node = self.__splits.get_node(path)
        node.value.direction = direction
        portion = 1.0 / (len(node.children) + 1)
        return self.__splits.insert(path, Split(portion, -1, rect2(), direction))

