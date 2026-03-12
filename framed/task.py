import asyncio
from dataclasses import dataclass
import enum
import threading
import typing
import queue
import time


T = typing.TypeVar("T")


class TaskStatus(enum.Enum):
    success = enum.auto()
    failure = enum.auto()
    custom  = enum.auto()


@dataclass(frozen=True)
class TaskResult(typing.Generic[T]):
    data: T
    process: typing.Callable[[T], typing.Any]


class TaskManager:
    __counter: int
    __pending: queue.Queue[tuple[typing.Callable[[int, typing.Any], typing.Coroutine], int, typing.Any]]
    __results: queue.Queue[tuple[int, TaskStatus, typing.Any]]
    __thread: threading.Thread | None
    __running: bool

    def __init__(self):
        self.__counter = 0
        self.__pending = queue.Queue()
        self.__results = queue.Queue()
        self.__thread = None
        self.__loop = None
        self.__running = True

    async def _wrap_coroutine(self, task_id: int, coro: typing.Coroutine):
        try:
            await coro
            status = TaskStatus.success
            error = None
        except BaseException as exc:
            status = TaskStatus.failure
            error = exc
        self.__results.put((task_id, status, error))

    async def _wrap_async_gen(self, task_id: int, generator: typing.AsyncGenerator):
        try:
            async for new_status in generator:
                self.__results.put((task_id, TaskStatus.custom, new_status))
            status = TaskStatus.success
            error = None
        except BaseException as exc:
            status = TaskStatus.failure
            error = exc
        self.__results.put((task_id, status, error))

    def dispatch_coroutine(self, coro: typing.Coroutine) -> int:
        return self.__dispatch(coro, self._wrap_coroutine)

    def dispatch_generator(self, asyncgen: typing.AsyncGenerator):
        return self.__dispatch(asyncgen, self._wrap_async_gen)

    def __dispatch(self, async_obj: typing.Any, wrapper: typing.Callable[[int, typing.Any], typing.Coroutine]):
        new_id = self.__counter
        self.__counter += 1
        if self.__thread is None:
            self.__start()
        self.__pending.put_nowait((wrapper, new_id, async_obj))
        return new_id

    def __start(self):
        self.__loop = asyncio.new_event_loop()
        self.__thread = threading.Thread(target=self.__run, args=(self.__loop,))
        self.__thread.start()

    def __run(self, loop):
        try:
            loop.run_until_complete(self.__poll(loop))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    async def __poll(self, loop):
        while self.__running:
            try:
                wrapper, new_id, async_obj = self.__pending.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0)
                continue
            task = wrapper(new_id, async_obj)
            loop.create_task(task)

    def close(self):
        self.__running = False
        if self.__thread is not None:
            self.__thread.join()

    def pull(self) -> tuple[int, TaskStatus, typing.Any] | None:
        if self.__results.empty():
            return None
        else:
            result = self.__results.get_nowait()
            return result

