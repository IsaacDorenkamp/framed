from __future__ import annotations
import typing
import weakref


T = typing.TypeVar("T")


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

    def _notify(self):
        for handler in self.__handlers:
            handler(self.__ptr._value)


class ContextValue(typing.Generic[T]):
    _value: T
    _type: type[T]
    _listeners: weakref.WeakSet[ContextRef[T]]
    def __init__(self, initial: T, type_: type[T]):
        self._value = initial
        self._type = type_
        self._listeners = weakref.WeakSet()

    def set(self, value: T):
        if value != self._value:
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

