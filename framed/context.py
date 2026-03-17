from __future__ import annotations
import contextlib
import typing
import weakref


T = typing.TypeVar("T")


class MutationValue(typing.Generic[T]):
    value: T
    __cancelled: bool
    def __init__(self, value: T):
        self.value = value
        self.__cancelled = False

    def cancel(self):
        self.__cancelled = True

    @property
    def cancelled(self) -> bool:
        return self.__cancelled


class ContextRef(typing.Generic[T]):
    __handlers: list[typing.Callable[[T], typing.Any]]
    __ptr: ContextValue[T]

    def __init__(self, pointer: ContextValue[T], _: type[T]):
        self.__ptr = pointer
        self.__handlers = []
        pointer._listeners.add(self)

    def set(self, value: T):
        self.__ptr.set(value)

    def get(self) -> T:
        return self.__ptr._value

    def handle(self, handler: typing.Callable[[T], typing.Any]):
        self.__handlers.append(handler)

    @contextlib.contextmanager
    def mutate(self) -> typing.Generator[MutationValue[T], None, None]:
        if self.__ptr._mutating:
            raise RuntimeError("Already mutating this ref's value!")
        self.__ptr._mutating = True
        previous = self.__ptr._value
        try:
            value = MutationValue(self.__ptr._value)
            yield value
            if not value.cancelled:
                self.set(value.value)
        except:
            self.__ptr._value = previous
            raise 
        finally:
            self.__ptr._mutating = False
    def _notify(self):
        for handler in self.__handlers:
            handler(self.__ptr._value)


class ContextValue(typing.Generic[T]):
    _mutating: bool
    _value: T
    _type: type[T]
    _listeners: weakref.WeakSet[ContextRef[T]]
    def __init__(self, initial: T, type_: type[T]):
        self._mutating = False
        self._value = initial
        self._type = type_
        self._listeners = weakref.WeakSet()

    def set(self, value: T):
        self._value = value
        for listener in self._listeners:
            listener._notify()

    @property
    def type(self) -> type[T]:
        return self._type


class Context:
    __vars: dict[str, ContextValue]

    def __init__(self):
        self.__vars = {}

    def create_var(self, name: str, value: T, vartype: type[T]):
        if name in self.__vars:
            raise ValueError(f"context var '{name}' already exists")
        self.__vars[name] = ContextValue[T](value, vartype)

    def __getattr__(self, attr: str):
        if attr in self.__vars:
            var = self.__vars[attr]
            return var._value

    def ref(self, attr: str):
        if attr not in self.__vars:
            raise AttributeError(f"no such context var {attr}")
        var = self.__vars[attr]
        return ContextRef(var, var.type)

    def __setattr__(self, attr: str, value: object):
        if attr.startswith("_"):
            object.__setattr__(self, attr, value)
            return
        if attr not in self.__vars:
            raise AttributeError(f"no such context var '{attr}'")
        var = self.__vars[attr]
        if not isinstance(value, var.type):
            raise TypeError(f"value '{value}' (type {type(value)}) does not match type {var.type}")
        var.set(value)

    @contextlib.contextmanager
    def mutate(self, attr: str) -> typing.Generator[MutationValue, None, None]:
        if attr not in self.__vars:
            raise AttributeError(f"no such context var {attr}")
        var = self.__vars[attr]
        ref = ContextRef(var, var._type)
        with ref.mutate() as m:
            yield m

