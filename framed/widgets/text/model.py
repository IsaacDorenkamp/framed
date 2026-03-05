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

    def clone(self) -> TextLocation:
        return TextLocation(line=self.line, col=self.col)


@dataclass
class TextRange:
    start: TextLocation
    end: TextLocation

    @property
    def valid(self) -> bool:
        return self.end >= self.start


@dataclass
class InsertResult:
    after: TextLocation
    remainder: str | None = None


class TextModel(metaclass=ABCMeta):
    def __init__(self, text: str = ""):
        pass

    @abstractmethod
    def get(self, region: TextRange | None = None) -> str:
        raise NotImplementedError()

    @abstractmethod
    def assign(self, text: str) -> TextLocation:
        pass

    @abstractmethod
    def insert(self, location: TextLocation, text: str) -> InsertResult:
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

    @abstractmethod
    def traverse(self, location: TextLocation, delta: int) -> TextLocation | None:
        raise NotImplementedError()

    @abstractmethod
    def has(self, location: TextLocation) -> bool:
        raise NotImplementedError()


# Implementations
class TextModelError(Exception):
    pass


class LineTextModel(TextModel):
    __text: str

    def __init__(self, text: str = ""):
        self.__text = text.split("\n")[0]

    def get(self, region: TextRange | None = None) -> str:
        if region is None:
            return self.__text

        if not region.valid:
            raise TextModelError(f"invalid region: {region}")

        start = region.start
        end = region.end
        if end.line > 0:
            raise TextModelError(f"line '{end.line}' out of range")

        return self.__text[start.col:end.col]

    def assign(self, text: str) -> TextLocation:
        self.__text = text.split("\n")[0]
        return TextLocation(line=0, col=len(self.__text))

    def insert(self, location: TextLocation, text: str):
        if location.line > 0:
            raise TextModelError(f"line '{location.line}' out of range")

        if location.col > len(self.__text):
            raise TextModelError(f"column '{location.col}' out of range")

        if "\n" in text:
            raise TextModelError("cannot insert newline into single-line model!")

        self.__text = self.__text[:location.col] + text + self.__text[location.col:]

        return InsertResult(after=TextLocation(line=0, col=location.col + len(text)))

    def delete(self, region: TextRange):
        if not region.valid:
            raise TextModelError(f"invalid region: {region}")

        start = region.start
        end = region.end
        if end.line > 0:
            raise TextModelError(f"line '{end.line}' out of range")

        if end.col > len(self.__text):
            raise TextModelError(f"column '{end.col}' out of range")

        self.__text = self.__text[:start.col] + self.__text[end.col:]

    @property
    def lines(self) -> int:
        return 1

    def get_line_length(self, line: int):
        if line > 0:
            raise TextModelError(f"line '{line}' out of range")

        return len(self.__text)

    def traverse(self, location: TextLocation, delta: int) -> TextLocation | None:
        if not self.has(location):
            raise TextModelError(f"location '{location}' out of range")

        result = location.clone()

        reverse = delta < 0
        delta = abs(delta)
        while delta > 0:
            if reverse:
                if result.col == 0:
                    return None
                else:
                    result.col -= 1
            else:
                if result.col >= len(self.__text):
                    return None
                else:
                    result.col += 1

            delta -= 1

        return result

    def has(self, location: TextLocation) -> bool:
        if location.line > 0:
            return False

        return location.col <= len(self.__text)


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
            if end.col > len(line):
                raise TextModelError(f"column '{end.col}' out of range for line '{line}'")

            return line[start.col:end.col]
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
                    result.write("\n" + line[:end.col])
                else:
                    result.write("\n" + line)
            return result.getvalue()

    def assign(self, text: str) -> TextLocation:
        self.__lines = text.split("\n")
        return TextLocation(line=len(self.__lines) - 1, col=len(self.__lines[-1]))

    def insert(self, location: TextLocation, text: str):
        if location.line > len(self.__lines):
            raise TextModelError(f"line '{location.line}' out of range")
        elif location.line == len(self.__lines):
            if location.col > 0:
                raise TextModelError(f"col '{location.col}' out of range for line '{location.line}'")
            parts = text.split("\n")
            self.__lines.extend(parts)
            return InsertResult(after=TextLocation(line=location.line + len(parts) - 1, col=len(parts[-1])))

        line = self.__lines[location.line]
        if location.col > len(line):
            raise TextModelError(f"column '{location.col}' out of range for line '{location.line}'")
        elif line and location.col == len(line) and line[-1] == "\n":
            raise TextModelError(f"column '{location.col}' out of range for line '{location.line}'")

        parts = text.split("\n")
        if len(parts) == 1:
            # modifies a single line only
            self.__lines[location.line] = line[:location.col] + text + line[location.col:]
            end_col = location.col + len(text)
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
            end_col = len(parts[-1])

        return InsertResult(after=TextLocation(line=location.line + len(parts) - 1, col=end_col))
            
    def delete(self, region: TextRange):
        if not region.valid:
            raise TextModelError(f"Invalid region: {region}")

        start = region.start
        end = region.end

        if end.line >= len(self.__lines):
            raise TextModelError(f"line '{end.line}' out of range")

        if start.line == end.line:
            line = self.__lines[start.line]
            self.__lines[start.line] = line[:start.col] + line[end.col:]
            return

        line = self.__lines[start.line]
        self.__lines[start.line] = line[:start.col] + self.__lines[end.line][end.col:]
        for line_no in range(end.line, start.line, -1):
            del self.__lines[line_no]

    @property
    def lines(self) -> int:
        return len(self.__lines)

    def get_line_length(self, line: int):
        return len(self.__lines[line])

    def traverse(self, location: TextLocation, delta: int) -> TextLocation | None:
        if not self.has(location):
            raise ValueError(f"location {location} is not in the model.")

        result = location.clone()
        if delta == 0:
            return result

        reverse = delta < 0
        delta = abs(delta)
        while delta > 0:
            if reverse:
                if result.col == 0:
                    if result.line == 0:
                        return None
                    else:
                        result.line -= 1
                        result.col = len(self.__lines[result.line])
                else:
                    result.col -= 1
            else:
                line = self.__lines[result.line]
                if result.col == len(line):
                    if result.line == len(self.__lines) - 1:
                        return None
                    else:
                        result.line += 1
                        result.col = 0
                else:
                    result.col += 1

            delta -= 1

        return result

    def has(self, location: TextLocation):
        if location.line >= len(self.__lines):
            return False

        line = self.__lines[location.line]
        if location.col > len(line):
            return False

        return True

