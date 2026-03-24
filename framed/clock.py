from abc import ABCMeta, abstractmethod
import math
import time
import typing


class Clock:
    NS = 1_000_000_000
    DEFAULT_RESOLUTION: typing.ClassVar[int] = math.floor(NS / 30)

    __last_tick: int
    __time: int
    __resolution: int

    def __init__(self):
        self.__last_tick = -1
        self.__time = -1
        self.__resolution = Clock.DEFAULT_RESOLUTION

    def start(self):
        self.__last_tick = time.monotonic_ns()
        self.__time = 0

    def update(self, ticker: typing.Callable[[int], None]):
        now = time.monotonic_ns()
        diff = now - self.__last_tick
        self.__last_tick = now
        self.__time += diff

        while self.__time >= self.__resolution:
            self.__time -= self.__resolution
            ticker(self.__resolution)


class TickHandler(metaclass=ABCMeta):
    @abstractmethod
    def on_tick(self, dt: int):
        raise NotImplementedError()

