import pygame as pg

from robot import Robot
from constants import WIN_SIZE


class Simulation:
    def __init__(self) -> None:
        self.running: bool = False
        self.clock: pg.time.Clock = pg.time.Clock()
        self.surface: pg.Surface = pg.display.set_mode(WIN_SIZE)
        self.image: pg.Surface = pg.transform.scale(pg.image.load("room.png"), WIN_SIZE)
        self.robot: Robot = Robot(self, 15, (250, 600), 2)

    def __frame(self) -> None:
        self.clock.tick()

        self.surface.blit(self.image, (0, 0))

        self.robot.update()
        self.robot.draw()

        pg.display.set_caption(f"FPS: {self.clock.get_fps()} | Points: {len(self.robot.scanner.points_index.points)}")

    def __events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

    def run(self) -> None:
        self.running = True

        while self.running:
            self.__events()
            self.__frame()
            pg.display.flip()
