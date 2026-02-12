from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class vec2:
    y: int = 0
    x: int = 0

    def __add__(self, other: vec2) -> vec2:
        return vec2(self.y + other.y, self.x + other.x)

    def __sub__(self, other: vec2) -> vec2:
        return vec2(self.y - other.y, self.x - other.x)

    def __iter__(self):
        yield self.y
        yield self.x

    def __len__(self):
        return 2

    def __getitem__(self, index: int):
        if index == 0:
            return self.y
        elif index == 1:
            return self.x
        else:
            raise IndexError("Index out of range")


@dataclass(frozen=True)
class rect2:
    y: int = 0
    x: int = 0
    h: int = 0
    w: int = 0

    def decompose(self) -> tuple[vec2, vec2]:
        """
        Decompose this region into two vectors, size and position.
        """
        return vec2(self.h, self.w), vec2(self.y, self.x)

    @property
    def curses(self) -> tuple[int, int, int, int]:
        """
        A convenient utility for returning fields in the order
        height, width, y, x for use in calls to certain curses
        functions (like newwin) that use this ordering.
        """
        return self.h, self.w, self.y, self.x

