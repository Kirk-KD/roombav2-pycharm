from __future__ import annotations

from rtree import index
import math
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from simulation import Simulation
from constants import WIN_WIDTH, WIN_HEIGHT

import pygame as pg

from util import dx_dy, distance


class Point:
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.position: Tuple[float, float] = self.x, self.y

    def __eq__(self, other) -> bool:
        return self.x == other.x and self.y == other.y


class Line:
    def __init__(self, point1: Point, point2: Point) -> None:
        self.point_left: Point = min(point1, point2, key=lambda p: p.x)
        self.point_right: Point = max(point1, point2, key=lambda p: p.x)
        if self.point_right.x - self.point_left.x == 0:
            self.slope: float = float("inf")
        else:
            self.slope: float = (self.point_right.y - self.point_left.y) / (self.point_right.x - self.point_left.x)
        self.radians: float = math.atan(self.slope) if self.slope != float("inf") else math.radians(90)
        self.length: float = distance(self.point_left.x, self.point_left.y, self.point_right.x, self.point_right.y)

        min_x = self.point_left.x
        min_y = min(self.point_left.y, self.point_right.y)
        max_x = self.point_right.x
        max_y = max(self.point_left.y, self.point_right.y)
        self.bounding_box: Tuple[float, float, float, float] = min_x, min_y, max_x, max_y

    def join(self, other: Line) -> Line:
        points = [self.point_left, self.point_right, other.point_left, other.point_right]
        new_lines = []
        for i in range(3):
            for j in range(i + 1, 4):
                new_lines.append(Line(points[i], points[j]))

        return max(new_lines, key=lambda l: l.length)

    def distance(self, other: Line) -> float:
        ds = [distance(*self.point_left.position, *other.point_left.position),
              distance(*self.point_left.position, *other.point_right.position),
              distance(*self.point_right.position, *other.point_left.position),
              distance(*self.point_right.position, *other.point_right.position)]
        return min(ds)

    def distance_to_point(self, point: Point) -> Tuple[float, Point]:
        AB = [self.point_left.x - self.point_right.x, self.point_left.y - self.point_right.y]
        BE = [point.x - self.point_left.x, point.y - self.point_left.y]
        AE = [point.x - self.point_right.x, point.y - self.point_right.y]

        AB_BE = AB[0] * BE[0] + AB[1] * BE[1]
        AB_AE = AB[0] * AE[0] + AB[1] * AE[1]

        if AB_BE > 0:
            closest_point = self.point_left
            y = point.y - self.point_left.y
            x = point.x - self.point_left.x
            ans = math.sqrt(x * x + y * y)
        elif AB_AE < 0:
            closest_point = self.point_right
            y = point.y - self.point_right.y
            x = point.x - self.point_right.x
            ans = math.sqrt(x * x + y * y)
        else:
            x1 = AB[0]
            y1 = AB[1]
            x2 = AE[0]
            y2 = AE[1]
            mod = math.sqrt(x1 * x1 + y1 * y1)
            ans = abs(x1 * y2 - y1 * x2) / mod
            closest_point = Point(self.point_left.x + AB_BE * AB[0] / mod ** 2,
                                  self.point_left.y + AB_BE * AB[1] / mod ** 2)

        return ans, closest_point


class PointsIndex:
    def __init__(self):
        p = index.Property()
        p.dimension = 2
        self.index: index.Index = index.Index(properties=p)
        self.points: List[Point] = []

    def add(self, point: Point):
        self.points.append(point)
        self.index.insert(len(self.points), (point.x, point.y, point.x, point.y), obj=point)

    def get(self, x: float, y: float):
        return list(self.index.intersection((x, y, x, y), objects=True))[0].object

    def get_closest(self, x: float, y: float, exclude_self: bool = False):
        points = self.index.nearest((x, y, x, y), objects=True, num_results=2)

        filtered = filter(lambda p: exclude_self is False or p.object.x != x or p.object.y != y, points)
        n = next(filtered, None)
        return n.object if n is not None else n

    def get_closest_except(self, x: float, y: float, ignored: List[Point]):
        points = self.index.nearest((x, y, x, y), objects=True, num_results=len(ignored) + 1)
        return next(filter(lambda p: p.object not in ignored, points)).object


class LinesIndex:
    pass


class Raycast:
    def __init__(self, surface: pg.Surface, max_dist: float, hop_dist: float, color_mask: Tuple[int, int, int]) -> None:
        self.surface: pg.Surface = surface
        self.max_dist: float = max_dist
        self.hop_dist: float = hop_dist
        self.color_mask: Tuple[int, int, int] = color_mask

    def ray(self, starting_position: Tuple[float, float], rad: float) -> Tuple[float, float] | None:
        """
        Cast a ray starting from `starting_position` at an angle of `rad`, in radians.

        :param starting_position: The starting position of the ray
        :param rad: The angle in radians
        :return: The hit point.
        """
        x, y = starting_position
        dx, dy = dx_dy(self.hop_dist, rad)
        dx_small, dy_small = dx_dy(1, rad)

        while (distance(starting_position[0], starting_position[1], x, y) < self.max_dist and
               0 <= x < WIN_WIDTH and 0 <= y < WIN_HEIGHT):
            pixel_x = int(x)
            pixel_y = int(y)
            if self.surface.get_at((pixel_x, pixel_y)) == self.color_mask:
                while pixel_x != starting_position[0] or pixel_y != starting_position[1]:
                    pixel_x = int(x)
                    pixel_y = int(y)
                    if self.surface.get_at((pixel_x, pixel_y)) != self.color_mask:
                        return x, y

                    x -= dx_small
                    y -= dy_small
                return x, y

            x += dx
            y += dy

        return None


class Scanner:
    def __init__(self, simulation: Simulation) -> None:
        self.simulation: Simulation = simulation
        self.raycast: Raycast = Raycast(self.simulation.surface, 300, 5, (255, 255, 255))
        self.result_lines: List[Line] = []
        self.points_index: PointsIndex = PointsIndex()

    def closest_point_on_line(self, point: Point):
        return min([line.distance_to_point(point) for line in self.result_lines], key=lambda x: x[0])

    def scan(self) -> None:
        self.result_lines = []

        # cast rays in all directions
        for i in range(0, 360 * 2 + 1):
            deg = i / 2
            xy = self.raycast.ray(self.simulation.robot.position, math.radians(deg))
            if not xy:
                continue
            x, y = xy

            point = Point(x, y)  # create the point
            closest = self.points_index.get_closest(x, y)  # get the closest point
            if closest and distance(*closest.position, x, y) <= 7:  # if the point is too close to an existing line
                continue
            self.points_index.add(point)

        visited_points = []
        point = self.points_index.points[0]
        while len(visited_points) != len(self.points_index.points) - 1:
            visited_points.append(point)
            closest = self.points_index.get_closest_except(point.x, point.y, visited_points)
            if distance(closest.x, closest.y, point.x, point.y) <= self.simulation.robot.radius:
                self.result_lines.append(Line(point, closest))
            point = closest

        updated_lines = []
        current_line = None
        for i in range(len(self.result_lines)):
            line = self.result_lines[i]

            if current_line is None:
                current_line = line
                continue

            if abs(line.radians - current_line.radians) <= math.radians(5) and line.distance(current_line) <= 10:
                current_line = current_line.join(line)
            else:
                updated_lines.append(current_line)
                current_line = line

        self.result_lines = updated_lines

    def draw_dots(self) -> None:
        for point in self.points_index.points:
            pg.draw.circle(self.simulation.surface, (0, 255, 0), point.position, 3)
        # ...

    def draw_lines(self) -> None:
        for line in self.result_lines:
            pg.draw.line(self.simulation.surface, (72, 28, 232),
                         line.point_left.position, line.point_right.position, 3)
            pg.draw.circle(self.simulation.surface, (0, 255, 0), line.point_left.position, 2)
            pg.draw.circle(self.simulation.surface, (0, 255, 0), line.point_right.position, 2)