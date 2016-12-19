import math
import operator
from time import sleep

import pygame
import pyscroll
import pytmx
from astar import AStar
from pygame.locals import *
from pytmx.util_pygame import load_pygame

FPS = 60
MOVEMENT_DELAY = 0.5
MAP_FILE = 'map.tmx'
PLAYER_IMAGE = 'player.png'


# simple wrapper to keep the screen resizeable
def init_screen(width, height):
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    return screen


class Player(pygame.sprite.Sprite):
    """A simple class to structure the player object"""

    def __init__(self, filename):
        super().__init__()
        self.image = pygame.image.load(filename).convert_alpha()
        self.rect = self.image.get_rect()

        # private variables
        self._position = [0, 0]

    @property
    def position(self):
        return tuple(self._position)

    @position.setter
    def position(self, value):
        self._position = list(value)
        self.rect.topleft = self._position


class Pathfinder(AStar):
    """A pathfinder class to implement moving in 2d space and a 'node' is just a (x,y) tuple that represents a reachable position"""

    def __init__(self, mesh):
        self.width = mesh.width
        self.height = mesh.height

    def heuristic_cost_estimate(self, n1, n2):
        """computes the 'direct' distance between two (x,y) tuples"""
        (x1, y1) = n1
        (x2, y2) = n2
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def distance_between(self, n1, n2):
        """this method always returns 1, as two 'neighbors' are always adjacent"""
        return 1

    def neighbors(self, node):
        """for a given coordinate on the mesh, returns up to 8 adjacent nodes that can be reached (=any adjacent coordinate that is walkable)"""
        x, y = node
        for i, j in [(0, -1), (0, +1), (-1, 0), (+1, 0), (-1, -1), (+1, -1), (+1, +1), (-1, +1)]:
            x1 = x + i
            y1 = y + j
            if x1 > 0 and y1 > 0 and x1 < self.width and y1 < self.height:
                # TODO: add obstacle detection
                yield (x1, y1)


class RandomGame(object):
    """init the game, set up the screen and the map with the player"""

    def __init__(self, mapfile):
        # create a double-ended queue to hold player path
        self._move_queue = collections.deque()
        self.running = False
        self.last_position_update = 0
        map = load_pygame(mapfile)
        # create new data source for pyscroll
        map_data = pyscroll.data.TiledMapData(map)

        w, h = screen.get_size()

        # create new renderer (camera)
        # clamp_camera is used to prevent the map from scrolling past the edge
        self.map_layer = pyscroll.BufferedRenderer(map_data, screen.get_size(), clamp_camera=True)

        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=2)
        self.map_layer.zoom = .5

        self.player = Player(PLAYER_IMAGE)
        self.player.position = self.map_layer.map_rect.center
        # add the player to the group
        self.group.add(self.player)

        # initialize the nav mesh
        self.mesh = Pathfinder(map)

    def draw(self, surface):
        # center the map/screen on the player
        self.group.center(self.player.rect.center)

        # draw the map and all sprites
        self.group.draw(surface)

    def handle_input(self):
        """ Handle pygame input events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                break

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                    pygame.exit()
                    break

                if event.key == K_SPACE:
                    tile_position = tuple(map(operator.floordiv, self.player.position, self.map_layer.data.tile_size))
                    self._move_queue.extend(self.mesh.astar(tile_position, (5, 5)))
                # TODO: input move coordinates

            # this will be handled if the window is resized
            elif event.type == VIDEORESIZE:
                init_screen(event.w, event.h)
                self.map_layer.set_size((event.w / 2, event.h / 2))

    def update(self, dt):
        """ Tasks that occur over time should be handled here"""
        self.last_position_update += dt
        if self.last_position_update >= MOVEMENT_DELAY:
            if self._move_queue.count() != 0:
                self.player.position = list(map(operator.mul, self._move_queue.popleft(), self.map_layer.data.tile_size))

            self.last_position_update = 0
        # TODO: idle animations etc.

    def run(self):
        """ Run the game loop"""
        clock = pygame.time.Clock()
        self.running = True

        try:
            while self.running:
                dt = clock.tick(FPS) / 1000.
                self.handle_input()
                self.update(dt)
                self.draw(screen)
                pygame.display.flip()

        except KeyboardInterrupt:
            self.running = False
            pygame.exit()


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    screen = init_screen(800, 600)
    pygame.display.set_caption('Moving X on the desert')

    try:
        game = RandomGame(MAP_FILE)
        game.run()
    except:
        pygame.quit()
        raise
