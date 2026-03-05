from __future__ import annotations
import typing


class Event:
    tag: typing.ClassVar[str] = "Event"

    __source: Widget
    def __init__(self, source: Widget):
        self.__source = source

    @property
    def source(self) -> Widget:
        return self.__source


if typing.TYPE_CHECKING:
    from ..widgets import Widget

