import asyncio
import enum
import threading
import typing
import queue


T = typing.TypeVar("T")


class TaskStatus(enum.Enum):
    success = enum.auto()
    failure = enum.auto()


class _Task(typing.Generic[T]):
    task_id: int
    lock: threading.Lock
    done: bool
    result: T | None
    error: BaseException | None
    status: TaskStatus
    callbacks: list[typing.Callable[[T], typing.Any]]
    fallbacks: list[typing.Callable[[BaseException], typing.Any]]

    def __init__(self, task_id: int):
        self.task_id = task_id
        self.lock = threading.Lock()
        self.done = False
        self.result = None
        self.error = None
        self.callbacks = []
        self.fallbacks = []

    def __await__(self):
        waiting = True
        while waiting:
            acquired = self.lock.acquire(blocking=False)
            if acquired:
                break
            yield

        self.lock.release()

    def close(self, status: TaskStatus, extra: T | BaseException):
        self.done = True
        self.status = status
        if status == TaskStatus.success:
            self.result = typing.cast(T, extra)
        else:
            self.error = typing.cast(BaseException, extra)

    def fulfill(self):
        errors = []

        if self.status == TaskStatus.success:
            self.result = typing.cast(T, self.result)
            for callback in self.callbacks:
                try:
                    callback(self.result)
                except BaseException as exc:
                    errors.append(exc)
        else:
            for callback in self.fallbacks:
                try:
                    callback(typing.cast(BaseException, self.error))
                except BaseException as exc:
                    errors.append(exc)

        if errors:
            if len(errors) == 1:
                raise errors[0]
            else:
                raise ExceptionGroup(*errors)


class Task(typing.Generic[T]):
    __task_impl: _Task
    def __init__(self, task_impl: _Task):
        self.__task_impl = task_impl

    def __await__(self):
        yield from self.__task_impl.__await__()

    def after(self, callback: typing.Callable[[T], typing.Any]):
        if self.__task_impl.done and self.__task_impl.status == TaskStatus.success:
            callback(typing.cast(T, self.__task_impl.result))
        elif not self.__task_impl.done:
            self.__task_impl.callbacks.append(callback)

    def catch(self, callback: typing.Callable[[BaseException], typing.Any]):
        if self.__task_impl.done and self.__task_impl.status == TaskStatus.failure:
            callback(typing.cast(BaseException, self.__task_impl.error))
        elif not self.__task_impl.done:
            self.__task_impl.fallbacks.append(callback)


class TaskManager:
    __counter: int
    __pending: queue.Queue[tuple[typing.Callable[[_Task, typing.Any], typing.Coroutine], _Task, typing.Any]]
    __completed: queue.Queue[_Task]
    __tasks: dict[int, _Task]
    __thread: threading.Thread | None
    __running: bool

    def __init__(self):
        self.__counter = 0
        self.__pending = queue.Queue()
        self.__completed = queue.Queue()
        self.__tasks = {}
        self.__thread = None
        self.__loop = None
        self.__running = True

    async def _wrap_coroutine(self, task: _Task, coro: typing.Coroutine):
        try:
            extra = await coro
            status = TaskStatus.success
        except BaseException as exc:
            extra = exc
            status = TaskStatus.failure

        t = self.__tasks[task.task_id]
        t.close(status, extra)
        self.__completed.put_nowait(t)
        del self.__tasks[task.task_id]

    async def _wrap_async_gen(self, task: _Task, generator: typing.AsyncGenerator):
        try:
            async for new_status in generator:
                # TODO: report in-progress statuses somehow
                pass
            extra = None
            status = TaskStatus.success
        except BaseException as exc:
            extra = exc
            status = TaskStatus.failure

        t = self.__tasks[task.task_id]
        t.close(status, extra)
        self.__completed.put_nowait(t)
        del self.__tasks[task.task_id]

    def dispatch_coroutine(self, coro: typing.Coroutine) -> Task:
        return Task(self.__dispatch(coro, self._wrap_coroutine))

    def dispatch_generator(self, asyncgen: typing.AsyncGenerator) -> Task:
        return Task(self.__dispatch(asyncgen, self._wrap_async_gen))

    def __dispatch(self, async_obj: typing.Any, wrapper: typing.Callable[[_Task, typing.Any], typing.Coroutine]) -> _Task:
        new_id = self.__counter
        self.__counter += 1
        if self.__thread is None:
            self.__start()
        t = self.__tasks[new_id] = _Task(new_id)
        t.lock.acquire()
        self.__pending.put_nowait((wrapper, t, async_obj))
        return t

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
                wrapper, task, async_obj = self.__pending.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0)
                continue
            aio_task = wrapper(task, async_obj)
            loop.create_task(aio_task)

    def close(self):
        self.__running = False
        if self.__thread is not None:
            self.__thread.join()

    def iter_complete(self):
        while not self.__completed.empty():
            try:
                yield self.__completed.get_nowait()
            except GeneratorExit:
                break

