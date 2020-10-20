from enum import IntEnum


class Color:
    Red = (0, 0, 255)
    Lime = (0, 255, 0)
    Blue = (255, 0, 0)
    LightBlue = (170, 178, 32)
    Yellow = (0, 255, 255)
    Cyan = (255, 255, 0)
    Magenta = (255, 0, 255)
    Orange = (0, 140, 255)
    Olive = (35, 142, 107)
    Green = (0, 128, 0)
    Purple = (211, 0, 148)
    Pink = (180, 20, 255)
    Black = (0, 0, 0)
    White = (255, 255, 255)
    Gray = (192, 192, 192)
    Brown = (19, 69, 139)


class ClassLabel:
    IN_VEST_IN_HARDHAT = "with_vest_and_helmet"
    IN_VEST_NO_HARDHAT = "with_vest"
    NO_VEST_IN_HARDHAT = "with_helmet"
    NO_VEST_NO_HARDHAT = "person"
    INVISIBLE_IN_VEST = "invisible_in_vest"
    INVISIBLE_NO_VEST = "invisible_no_vest"


DEFAULT_CLASS_LABEL = ClassLabel.IN_VEST_IN_HARDHAT
DEFAULT_INVISIBLE_LABEL = ClassLabel.INVISIBLE_NO_VEST


class HotKey:
    SetDrawMode = ord("w")
    SetDeletionMode = ord("d")
    SetModeChangeName = ord("i")
    SaveAndOpenNext = ord("y")
    SkipImage = ord("n")
    Quit = ord("q")
    UndoLabeling = ord("r")


ClassHotKeys = {
    ord("0"): ClassLabel.NO_VEST_NO_HARDHAT,
    ord("1"): ClassLabel.NO_VEST_IN_HARDHAT,
    ord("2"): ClassLabel.IN_VEST_NO_HARDHAT,
    ord("3"): ClassLabel.IN_VEST_IN_HARDHAT,
    ord("4"): ClassLabel.INVISIBLE_NO_VEST,
    ord("5"): ClassLabel.INVISIBLE_IN_VEST,
}


class LabelingMode(IntEnum):
    DELETION = 1
    DRAWING = 2
    SET_LABEL = 3


CLASS_COLORS = {
    ClassLabel.INVISIBLE_NO_VEST: Color.Black,
    ClassLabel.INVISIBLE_IN_VEST: Color.Purple,
    ClassLabel.NO_VEST_NO_HARDHAT: Color.Red,
    ClassLabel.NO_VEST_IN_HARDHAT: Color.Yellow,
    ClassLabel.IN_VEST_NO_HARDHAT: Color.Blue,
    ClassLabel.IN_VEST_IN_HARDHAT: Color.Green,
}

LABEL_CATEGORY_ID = {
    ClassLabel.NO_VEST_NO_HARDHAT: 0,
    ClassLabel.NO_VEST_IN_HARDHAT: 1,
    ClassLabel.IN_VEST_NO_HARDHAT: 2,
    ClassLabel.IN_VEST_IN_HARDHAT: 3,
    ClassLabel.INVISIBLE_NO_VEST: 4,
    ClassLabel.INVISIBLE_IN_VEST: 5,
}

CATEGORY_ID_TO_LABEL = {
    0: ClassLabel.NO_VEST_NO_HARDHAT,
    1: ClassLabel.NO_VEST_IN_HARDHAT,
    2: ClassLabel.IN_VEST_NO_HARDHAT,
    3: ClassLabel.IN_VEST_IN_HARDHAT,
    4: ClassLabel.INVISIBLE_NO_VEST,
    5: ClassLabel.INVISIBLE_IN_VEST,
}

misspelling_correction = {
    "unvisible_in_vest": "invisible_in_vest",
    "unvisible_not_in_vest": "invisible_no_vest",
}


WINDOW_NAME = "Labeler"
BOLD_BBOX_LINE_THICKNESS = 5
DEFAULT_BBOX_LINE_THICKNESS = 3
TEXT_COLOR = Color.Cyan
TEXTTHICKNESS_IM_WIDTH_RATIO = 0.007
TEXTSIZE_IM_WIDTH_RATIO = 0.002