from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
import io


@dataclass
class TextLocation:
    line: int
    col: int

    def __eq__(self, other: object):
        if not isinstance(other, TextLocation):
            return False
        return self.line == other.line and self.col == other.col

    def __ne__(self, other: object):
        if not isinstance(other, TextLocation):
            return True
        return self.line != other.line or self.col != other.col

    def __gt__(self, other: TextLocation):
        if self.line > other.line:
            return True
        elif self.line == other.line:
            return self.col > other.col
        else:
            return False

    def __ge__(self, other: TextLocation):
        return (
            self == other or
            self > other
        )

    def __lt__(self, other: TextLocation):
        if self.line < other.line:
            return True
        elif self.line == other.line:
            return self.col < other.line
        else:
            return False

    def __le__(self, other: TextLocation):
        return (
            self == other or
            self < other
        )


@dataclass
class TextRange:
    start: TextLocation
    end: TextLocation

    @property
    def valid(self) -> bool:
        return self.end >= self.start


class TextModel(metaclass=ABCMeta):
    def __init__(self, text: str = ""):
        pass

    @abstractmethod
    def get(self, region: TextRange | None = None) -> str:
        raise NotImplementedError()

    @abstractmethod
    def insert(self, location: TextLocation, text: str):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, region: TextRange):
        raise NotImplementedError()

    @property
    @abstractmethod
    def lines(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def get_line_length(self, line: int):
        raise NotImplementedError()


# Implementations
class TextModelError(Exception):
    pass


class SimpleTextModel(TextModel):
    __lines: list[str]

    def __init__(self, text: str = ""):
        self.__lines = text.split("\n")

    def get(self, region: TextRange | None = None) -> str:
        if region is None:
            return "\n".join(self.__lines)

        if not region.valid:
            raise TextModelError(f"Invalid region: {region}")

        start = region.start
        end = region.end

        if end.line >= len(self.__lines):
            raise TextModelError(f"line '{end.line}' out of range")

        if start.line == end.line:
            line = start.line
            if line >= len(self.__lines):
                raise TextModelError(f"line '{line}' out of range")

            line = self.__lines[line]
            if end.col >= len(line):
                raise TextModelError(f"column '{end.col}' out of range for line '{line}'")

            return line[start.col:end.col+1]
        else:
            result = io.StringIO()
            for line_no in range(start.line, end.line+1):
                line = self.__lines[line_no]
                if line_no == start.line:
                    if start.col >= len(line):
                        raise TextModelError(f"column '{start.col}' out of range for line '{line}'")
                    result.write(line[start.col:])
                elif line_no == end.line:
                    if end.col > len(line):
                        raise TextModelError(f"column '{end.col}' out of range for line '{line}'")
                    result.write("\n" + line[:end.col+1])
                else:
                    result.write("\n" + line)
            return result.getvalue()

    def insert(self, location: TextLocation, text: str):
        if location.line > len(self.__lines):
            raise TextModelError(f"line '{location.line}' out of range")
        elif location.line == len(self.__lines):
            if location.col > 0:
                raise TextModelError(f"col '{location.col}' out of range for line '{location.line}'")
            self.__lines.extend(text.split("\n"))
            return

        line = self.__lines[location.line]
        if location.col > len(line):
            raise TextModelError(f"column '{location.col}' out of range for line '{location.line}'")
        elif line and location.col == len(line) and line[-1] == "\n":
            raise TextModelError(f"column '{location.col}' out of range for line '{location.line}'")

        parts = text.split("\n")
        if len(parts) == 1:
            # modifies a single line only
            self.__lines[location.line] = line[:location.col] + text + line[location.col:]
        else:
            # oh boy, multiple lines!
            line = self.__lines[location.line]
            del self.__lines[location.line]
            for index, part in enumerate(parts):
                if index == 0:
                    content = line[:location.col] + part
                elif index == len(parts) - 1:
                    content = part + line[location.col:]
                else:
                    content = part
                self.__lines.insert(location.line + index, content)
            
    def delete(self, region: TextRange):
        if not region.valid:
            raise TextModelError(f"Invalid region: {region}")

        start = region.start
        end = region.end

        if end.line >= len(self.__lines):
            raise TextModelError(f"line '{end.line}' out of range")

        replace_with = ""
        for line_no in range(end.line, start.line - 1, -1):
            line = self.__lines[line_no]
            if line_no == start.line:
                if start.col > len(line):
                    raise TextModelError(f"column '{start.col}' out of range for line '{start.line}'")
                replace_with = line[:start.col] + replace_with
            if line_no == end.line:
                if end.col > len(line):
                    raise TextModelError(f"column '{end.col}' out of range for line '{end.line}'")
                replace_with += line[end.col+1:]

            del self.__lines[line_no]

        self.__lines.insert(start.line, replace_with)

    @property
    def lines(self) -> int:
        return len(self.__lines)

    def get_line_length(self, line: int):
        return len(self.__lines[line])
