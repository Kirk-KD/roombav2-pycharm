from __future__ import annotations

import math
from typing import TYPE_CHECKING, Tuple

from constants import EXTRA_COLLISION

if TYPE_CHECKING:
    from simulation import Simulation
import pygame as pg
from enum import Enum

from util import line_end, dx_dy, distance
from scanner import Scanner, Point, Line


class Robot:
    class Action(Enum):
        POST_INIT = "POST_INIT"
        GO_TO_WALL = "GO_TO_WALL"
        GO_ALONG_WALL = "GO_ALONG_WALL"

    def __init__(self, simulation: Simulation, radius: float, position: Tuple[float, float], speed: float) -> None:
        self.simulation: Simulation = simulation
        self.radius: float = radius
        self.position: Tuple[float, float] = position
        self.speed: float = speed
        self.radians: float = 0

        self.action: Robot.Action = Robot.Action.POST_INIT
        self.closest_point: Point = ...

        self.scanner: Scanner = Scanner(self.simulation)

    def preview_forward(self, speed, rotation_rad: float = 0) -> Tuple[Tuple[float, float], float]:
        dx, dy = dx_dy(speed, self.radians + rotation_rad)
        position = self.position[0] + dx, self.position[1] + dy
        return position, self.radians + rotation_rad

    def collision(self, position: Tuple[float, float]) -> bool:
        return self.scanner.closest_point_on_line(Point(*position))[0] < self.radius

    def move_forward(self, rotation_rad: float = 0) -> bool:
        position, rotation = self.preview_forward(self.speed, rotation_rad=rotation_rad)
        if self.collision(position):
            return True
        self.position = position
        return False

    def draw(self) -> None:
        pg.draw.circle(self.simulation.surface, (255, 255, 0), self.position, self.radius, 2)
        pg.draw.line(self.simulation.surface, (255, 255, 255), self.position,
                     line_end(*self.position, self.radius, self.radians))

        # self.scanner.draw_dots()
        self.scanner.draw_lines()

    def update(self) -> None:
        self.scanner.scan()
        self.logics()

    def logics(self) -> None:
        """Perform all the logical operations per frame."""

        match self.action:
            case Robot.Action.POST_INIT:
                _, self.closest_point = self.scanner.closest_point_on_line(Point(*self.position))
                self.radians = Line(Point(*self.position), self.closest_point).radians - math.pi / 2
                self.action = Robot.Action.GO_TO_WALL

            case Robot.Action.GO_TO_WALL:
                pg.draw.circle(self.simulation.surface, (255, 0, 0), self.closest_point.position, 5)
                will_collide = self.move_forward()
                if will_collide:
                    self.radians += math.pi / 2
                    self.action = Robot.Action.GO_ALONG_WALL

            case Robot.Action.GO_ALONG_WALL:
                self.min_max_turn(math.radians(-0.2), turn_until_collision=True)

                collision = self.move_forward()
                if collision:
                    # self.radians += math.radians(4)
                    self.min_max_turn(math.radians(2), turn_until_collision=False)
                elif self.scanner.closest_point_on_line(Point(*self.position))[0] > self.radius + EXTRA_COLLISION:
                    self.radians -= math.radians(0.5)

    def min_max_turn(self, rad: float, turn_until_collision: bool) -> None:
        """
        Turn by `rad` (left or right) until the robot will/will not collide with a wall.

        :param rad: rotation in radians, negative is left, positive is right
        :param turn_until_collision: `True` to keep turning until collision, `False` to keep turning until no longer
            colliding with any walls
        :return: None
        """
        rot = 0
        p_pos, p_rot = self.position, self.radians
        while -math.radians(360) < rot < math.radians(360):
            rot += rad
            p, r = self.preview_forward(1, rot)
            if turn_until_collision:
                if self.collision(p_pos):
                    break
            else:
                if not self.collision(p_pos):
                    break
            p_pos, p_rot = p, r
        self.position = p_pos
        self.radians = p_rot
