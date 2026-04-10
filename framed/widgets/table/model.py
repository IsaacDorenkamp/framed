from abc import ABCMeta, abstractmethod
import typing


class OutOfRangeError(Exception):
    pass


class InvalidDataError(Exception):
    pass


class CannotResizeError(Exception):
    pass


class TableModel(metaclass=ABCMeta):
    @property
    @abstractmethod
    def rows(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def columns(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_rows(self, rows: int):
        raise NotImplementedError()

    @abstractmethod
    def set_columns(self, cols: int):
        raise NotImplementedError()

    @abstractmethod
    def delete_row(self, row: int):
        raise NotImplementedError()

    @abstractmethod
    def delete_column(self, col: int):
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


class TableTextModel(TableModel):
    __data: dict[tuple[int, int], str]
    __rows: int
    __cols: int

    def __init__(self):
        self.__rows = 1
        self.__cols = 1
        self.__data = {}

    @property
    def rows(self) -> int:
        return self.__rows

    @property
    def columns(self) -> int:
        return self.__cols

    def set_rows(self, rows: int):
        self.__rows = rows
        del_keys = [key for key in self.__data.keys() if key[0] >= rows]
        for key in del_keys:
            del self.__data[key]

    def set_columns(self, cols: int):
        self.__cols = cols
        del_keys = [key for key in self.__data.keys() if key[1] >= cols]
        for key in del_keys:
            del self.__data[key]

    def delete_row(self, row: int):
        if row < 0 or row >= self.__rows:
            raise OutOfRangeError(f"row out of range: {row}")
        del_keys = [key for key in self.__data.keys() if key[0] == row]
        shift_keys = [key for key in self.__data.keys() if key[0] > row]
        for del_key in del_keys:
            del self.__data[del_key]
        for shift_key in shift_keys:
            self.__data[(shift_key[0] - 1, shift_key[1])] = self.__data.pop(shift_key)
        self.__rows -= 1

    def delete_column(self, col: int):
        if col < 0 or col >= self.__cols:
            raise OutOfRangeError(f"col out of range: {col}")
        del_keys = [key for key in self.__data.keys() if key[1] == col]
        shift_keys = [key for key in self.__data.keys() if key[1] > col]
        for del_key in del_keys:
            del self.__data[del_key]
        for shift_key in shift_keys:
            self.__data[(shift_key[0], shift_key[1] - 1)] = self.__data.pop(shift_key)

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

