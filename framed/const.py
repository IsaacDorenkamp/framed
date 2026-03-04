from enum import IntEnum


class HAlign(IntEnum):
    LEFT = -1
    CENTER = 0
    RIGHT = 1

    def get_offset(self, space: int):
        match self:
            case HAlign.LEFT:
                return 0
            case HAlign.CENTER:
                return space // 2
            case HAlign.RIGHT:
                return space


class VAlign(IntEnum):
    TOP = -1
    CENTER = 0
    BOTTOM = 1

