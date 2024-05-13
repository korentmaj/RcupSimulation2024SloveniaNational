"""
    SERS TEAM
    detectable_filter.py
"""

import numpy as np
from detectables.color_filter import ColorFilter

"""
    ColorFilter((94, 112,  32), (95, 143, 139)) - Walls
    ColorFilter((0, 0, 192,), (0, 0, 192)) - Floor
    ColorFilter((0, 0, 29), (0, 0, 138)) - Obstacles
    ColorFilter((0, 0, 10), (0, 0, 30)) - Outer hole
    ColorFilter((0, 0, 106), (0, 0, 106)) - Inner hole
    ColorFilter((0, 205, 233), (0, 205, 233)) - Red tile
    ColorFilter((107, 0, 72), (116, 90, 211)) - Checkpoint
"""

class NonFixtureFilter:
    def __init__(self) -> None:
        self.color_filters = (
            ColorFilter((94, 112,  32), (95, 143, 139)),
            ColorFilter((0, 0, 192,), (0, 0, 192)),
            ColorFilter((0, 0, 29), (0, 0, 138)),
            ColorFilter((0, 0, 10), (0, 0, 30)),
            ColorFilter((0, 0, 106), (0, 0, 106)),
            ColorFilter((0, 205, 233), (0, 205, 233)),
            ColorFilter((107, 0, 72), (116, 90, 211))
        )

    def filter(self, image):
        base = np.zeros(image.shape[:2], np.bool_)
        for f in self.color_filters:
            filtered = f.filter(image).astype(np.bool_)
            base += filtered

        return base
