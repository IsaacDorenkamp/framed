from abc import ABCMeta, abstractmethod
import curses

from .panel import Panel
from .struct import vec2


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
        curses.doupdate()

    @abstractmethod
    def decorate(self):
        """
        Perform additional rendering tasks, such as drawing
        borders to visually separate panels.
        """
        raise NotImplementedError()

    @abstractmethod
    def set_size(self, size: vec2):
        """
        Fit contents of the manager to the specified size.
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

    def set_active_panel(self, active_index: int):
        if active_index >= len(self.__panels):
            raise ManagerError("active_index must be a valid index!")
        self.__active = active_index
        if self.__showing:
            self.__display()

    def set_size(self, size: vec2):
        for panel in self.__panels:
            panel.set_size(size)

