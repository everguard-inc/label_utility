import json
from typing import Dict, List, NoReturn, Union

import config as cfg


class Point:
    def __init__(self, x: int, y: int):
        self.x: int = x
        self.y: int = y


class BBox:
    def __init__(self, x1: int, y1: int, x2: int, y2: int, label: cfg.ClassLabel):
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2
        self.label: cfg.ClassLabel = label

    def __contains__(self, item: Point):
        if self.x1 <= item.x <= self.x2 and self.y1 <= item.y <= self.y2:
            return True
        return False