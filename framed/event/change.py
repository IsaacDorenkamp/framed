import typing

from .event import Event
from ..widgets.widget import Widget


T = typing.TypeVar("T")


class ChangeEvent(Event, typing.Generic[T]):
    tag: typing.ClassVar[str] = "change"

    __value: T

    def __init__(self, source: Widget, value: T):
        super().__init__(source)
        self.__value = value

    @property
    def value(self) -> T:
        return self.__value

