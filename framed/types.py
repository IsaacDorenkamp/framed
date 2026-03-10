from dataclasses import dataclass
import typing


T = typing.TypeVar("T")


@dataclass(frozen=True)
class Message(typing.Generic[T]):
    name: str
    data: T

