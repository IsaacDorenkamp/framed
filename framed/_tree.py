from __future__ import annotations
from dataclasses import dataclass
import typing


class TreeError(Exception):
    pass


T = typing.TypeVar("T")


@dataclass
class _node(typing.Generic[T]):
    value: T
    children: list[_node[T]]


def _traverse(node: _node[T], path: tuple[int, ...] = ()):
    yield path, len(node.children) == 0, node.value
    for index, child in enumerate(node.children):
        yield from _traverse(child, path=path + (index,))


class _tree(typing.Generic[T]):
    __root: _node[T]

    def __init__(self, root: T):
        self.__root = _node(root, [])

    def __iter__(self) -> typing.Generator[tuple[tuple[int, ...], bool, T], None, None]:
        yield from _traverse(self.__root)

    def insert(self, path: tuple[int, ...], value: T, at: int = -1) -> tuple[int, ...]:
        node = self.__root
        for index in path:
            try:
                node = node.children[index]
            except IndexError:
                raise TreeError("Node at path '%s' does not exist" % str(path))

        if at == -1:
            node.children.append(_node(value, []))
            at = len(node.children) - 1
        else:
            try:
                node.children.insert(at, _node(value, []))
            except IndexError:
                raise TreeError("Node at path '%s' cannot insert at index '%d'" % (str(path), at))

        return path + (at,)

    def remove(self, path: tuple[int, ...], prune: bool = False):
        node = self.__root
        for index in path[:-1]:
            try:
                node = node.children[index]
            except IndexError:
                raise TreeError("Node at path '%s' does not exist" % str(path))

        final_index = path[-1]
        if not prune:
            try:
                check = node.children[final_index]
                if len(check.children) > 0:
                    raise TreeError("Node at path '%s' is not a leaf!" % str(path))
            except IndexError:
                raise TreeError("Node at path '%s' does not exist" % str(path))

        try:
            node.children.pop(final_index)
        except IndexError:
            raise TreeError("Node at path '%s' does not exist" % str(path))

    def get_node(self, path: tuple[int, ...]) -> _node[T]:
        node = self.__root
        for index in path:
            try:
                node = node.children[index]
            except IndexError:
                raise TreeError("Node at path '%s' does not exist" % str(path))
        return node


    def get(self, path: tuple[int, ...]) -> T:
        return self.get_node(path).value

    def set(self, path: tuple[int, ...], value: T):
        node = self.__root
        for index in path:
            try:
                node = node.children[index]
            except IndexError:
                raise TreeError("Node at path '%s' does not exist" % str(path))
        node.value = value

    @property
    def root(self) -> _node[T]:
        return self.__root

