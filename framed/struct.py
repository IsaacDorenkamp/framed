class vec2:
    __slots__ = ['x', 'y']

    x: int
    y: int

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __add__(self, other: vec2) -> vec2:
        return vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: vec2) -> vec2:
        return vec2(self.x - other.x, self.y - other.y)

    def __iter__(self):
        yield self.x
        yield self.y

    def __len__(self):
        return 2

    def __getitem__(self, index: int):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Index out of range")

