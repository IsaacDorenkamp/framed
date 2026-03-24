from abc import ABCMeta, abstractmethod
import curses
import math

from ..clock import Clock, TickHandler
from ..struct import vec2
from .widget import Widget


class _progressmodel(metaclass=ABCMeta):
    width: int
    value: float

    def __init__(self, width: int):
        self.width = width
        self.value = 0.0

    def tick(self, dt: int):
        pass

    def set_value(self, value: float):
        self.value = min(1.0, max(0.0, value))

    @property
    @abstractmethod
    def content(self) -> str:
        raise NotImplementedError()


class _compact(_progressmodel):
    STAGES = [
        "\u2847", "\u280F", "\u281B", "\u2839",
        "\u28B8", "\u28F0", "\u28E4", "\u28C6"
    ]

    UPDATE_TIME = Clock.NS // 16

    stage: int
    elapsed: int

    def __init__(self, width: int):
        super().__init__(width)
        self.stage = 0
        self.elapsed = 0

    def tick(self, dt: int):
        self.elapsed += dt
        while self.elapsed >= _compact.UPDATE_TIME:
            self.elapsed -= _compact.UPDATE_TIME
            self.stage += 1
        self.stage %= 8

    @property
    def content(self) -> str:
        return _compact.STAGES[self.stage] * self.width


class _regular(_progressmodel):
    OFFSETS = [
        " \u2588",
        "\u2590\u258B",
    ]
    offset: int
    bar_width: int
    repeats: int
    elapsed: int

    UPDATE_TIME = Clock.NS // 32

    def __init__(self, width: int):
        super().__init__(width)
        self.offset = 0
        self.bar_width = min(7, width // 2)
        self.repeats = math.ceil(self.width / (self.bar_width * 2))
        self.elapsed = 0

    def tick(self, dt: int):
        self.elapsed += dt
        while self.elapsed >= _regular.UPDATE_TIME:
            self.elapsed -= _compact.UPDATE_TIME
            self.offset += 1
        self.offset %= self.bar_width * 4

    @property
    def content(self) -> str:
        should_offset = (self.offset % 2 == 1)
        if should_offset:
            bar = "\u2590" + ("\u2588" * (self.bar_width - 1)) + "\u258C"
        else:
            bar = "\u2588" * self.bar_width

        spaces = self.bar_width - (1 if should_offset else 0)
        overflow = (self.offset + 2 * self.bar_width) - (self.bar_width * 4)
        if overflow > 0:
            split = len(bar) - (overflow // 2) - (1 if should_offset else 0)
            segment = bar[split:] + (" " * spaces) + bar[:split]
        else:
            offset = self.offset // 2
            segment = (" " * offset) + bar + (" " * (spaces - offset))

        return segment * self.repeats


class _determinate(_progressmodel):
    PARTIALS = [
        "\u258F", "\u258E", "\u258D", "\u258C",
        "\u258B", "\u258A", "\u2589"
    ]

    blocks: int

    def __init__(self, width: int):
        super().__init__(width)
        self.blocks = width * 8

    @property
    def content(self) -> str:
        total_blocks = round(self.blocks * self.value)
        remainder = total_blocks % 8
        return ("\u2588" * (total_blocks // 8)) + (_determinate.PARTIALS[remainder - 1] if remainder > 0 else "")


class ProgressBar(Widget, TickHandler):
    __model: _progressmodel
    __determinate: bool
    __active: bool

    def __init__(self, determinate: bool = True):
        super().__init__()
        self.__determinate = determinate
        self.__active = True
        self.__create_model()

    def __create_model(self, value: float = 0.0):
        width = self.size[1]
        if self.__determinate:
            self.__model = _determinate(width)
        else:
            if width < 5:
                self.__model = _compact(width)
            else:
                self.__model = _regular(width)

        self.__model.set_value(value)

    def on_tick(self, dt: int):
        self.__model.tick(dt)
        self.invalidate()

    def set_size(self, size: vec2):
        super().set_size(size)
        self.__create_model(self.__model.value)

    def render(self):
        if self.__active:
            self._window.move(0, 0)
            try:
                self._window.addnstr(self.__model.content, self.size[1])
            except curses.error:
                pass

    @property
    def value(self) -> float:
        return self.__model.value

    def set_value(self, value: float):
        self.__model.set_value(value)
        self.invalidate()

    @property
    def active(self) -> bool:
        return self.__active

    @active.setter
    def active(self, active: bool):
        if active != self.__active:
            self.__active = active
            self.invalidate()

