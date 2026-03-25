from abc import ABCMeta, abstractmethod
import typing


class OutOfRangeError(Exception):
    pass


class InvalidDataError(Exception):
    pass


class Model(metaclass=ABCMeta):
    @property
    @abstractmethod
    def rows(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def columns(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def get_data(self, row: int, col: int) -> typing.Any:
        raise NotImplementedError()

    @abstractmethod
    def get_text(self, row: int, col: int) -> str:
        raise NotImplementedError()

    @abstractmethod
    def set_data(self, row: int, col: int, data: typing.Any):
        raise NotImplementedError()

    @abstractmethod
    def set_text(self, row: int, col: int, text: str):
        raise NotImplementedError()

    @abstractmethod
    def accept_edit(self, row: int, col: int, text: str):
        raise NotImplementedError()


class TextModel(Model):
    __data: dict[tuple[int, int], str]
    __rows: int
    __cols: int

    def __init__(self, rows: int, cols: int):
        if rows <= 0:
            raise ValueError(f"rows must be positive!")
        if cols <= 0:
            raise ValueError(f"cols must be positive!")
        self.__rows = rows
        self.__cols = cols

    @property
    def rows(self) -> int:
        return self.__rows

    @property
    def columns(self) -> int:
        return self.__cols

    def get_data(self, row: int, col: int) -> typing.Any:
        return self.get_text(row, col)

    def get_text(self, row: int, col: int) -> str:
        if row >= self.rows:
            raise OutOfRangeError(f"row '{row}' out of range")

        if col >= self.columns:
            raise OutOfRangeError(f"column '{col}' out of range")

        return self.__data.get((row, col), "")

    def set_data(self, row: int, col: int, data: typing.Any):
        if not isinstance(data, str):
            raise TypeError("data must be str")

        self.set_text(row, col, data)

    def set_text(self, row: int, col: int, text: str):
        if not text:
            self.__data.pop((row, col), None)
        else:
            self.__data[(row, col)] = text

    def accept_edit(self, row: int, col: int, text: str):
        self.set_text(row, col, text)

