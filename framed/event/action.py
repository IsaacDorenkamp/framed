from __future__ import annotations
import typing

from .event import Event


class ActionEvent(Event):
    tag = "action"

    def __init__(self, source: Widget):
        super().__init__(source)


if typing.TYPE_CHECKING:
    from ..widgets import Widget

