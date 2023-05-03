import math
from typing import Tuple


def dx_dy(d: float, rad: float) -> Tuple[float, float]:
    """
    Calculate the delta difference in x and y after traveling `d` units in the angle of `rad`.

    :param d: Distance
    :param rad: Angle in radians
    :return: The delta difference in x and y
    """
    return math.sin(rad) * d, math.cos(rad) * d


def line_end(x: float, y: float, d: float, rad: float) -> Tuple[float, float]:
    """
    Given the coordinates (`x`, `y`), the distance `d`, and the angle in radians `rad`, calculate the other end of the
    line segment.

    :param x: X value of the coordinates.
    :param y: Y value of the coordinates.
    :param d: The length of the line segment.
    :param rad: The angle in radians, where 0 is when the line is down and vertical.
    :return: A set of coordinates representing the end of the line segment.
    """
    dx, dy = dx_dy(d, rad)
    return x + dx, y + dy


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x1 - x2, y1 - y2)
