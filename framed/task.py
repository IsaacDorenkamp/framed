import asyncio
import enum
import threading
import typing

from . import _log


T = typing.TypeVar("T")


class TaskStatus(enum.Enum):
    success = enum.auto()
    failure = enum.auto()
    custom  = enum.auto()


class TaskManager:
    __counter: int
    __results: asyncio.Queue[tuple[int, TaskStatus, typing.Any]]
    __thread: threading.Thread | None

    def __init__(self):
        self.__counter = 0
        self.__loop = asyncio.new_event_loop()
        self.__results = asyncio.Queue()
        self.__thread = None

    async def _wrap_coroutine(self, task_id: int, coro: typing.Coroutine):
        try:
            await coro
            status = TaskStatus.success
            error = None
        except BaseException as exc:
            status = TaskStatus.failure
            error = exc
        await self.__results.put((task_id, status, error))

    async def _wrap_async_gen(self, task_id: int, generator: typing.AsyncGenerator):
        try:
            async for new_status in generator:
                await self.__results.put((task_id, TaskStatus.custom, new_status))
            status = TaskStatus.success
            error = None
        except BaseException as exc:
            status = TaskStatus.failure
            error = exc
        await self.__results.put((task_id, status, error))

    def dispatch_coroutine(self, coro: typing.Coroutine) -> int:
        new_id = self.__counter
        self.__counter += 1
        self.__loop.create_task(self._wrap_coroutine(new_id, coro))
        return new_id

    def dispatch_generator(self, asyncgen: typing.AsyncGenerator):
        new_id = self.__counter
        self.__counter += 1
        self.__loop.create_task(self._wrap_async_gen(new_id, asyncgen))
        return new_id

    def __start(self):
        self.__thread = threading.Thread(target=self.__loop.run_forever)
        self.__thread.start()

    def close(self):
        if self.__loop.is_running():
            self.__loop.run_until_complete(self.__loop.shutdown_asyncgens())
            self.__loop.close()

    def reap(self) -> typing.Generator[tuple[int, TaskStatus, typing.Any], None, None]:
        while not self.__results.empty():
            try:
                yield self.__results.get_nowait()
            except asyncio.QueueEmpty:
                break

