#!/usr/bin/env python3

import tdl
import random
from tdl import noise
from math import sin, cos
from collections import deque, namedtuple

import data
from data import colors

###############################################################################
#       Constants                                                             #
###############################################################################

# names and appearances of Tiles
TILE_NAMES = ['dark_ground','dark_wall']
TILE_CHARS = ['.','#']

BIOME_NAMES = ['OCEAN','BEACH','DESERT','GRASSLAND','FOREST',
               'RAINFOREST','TAIGA','BARE','TUNDRA','SNOW']

pi = 3.14159265359

###############################################################################
#       Functions                                                             #
###############################################################################

def get_biome(e,m):
    # e = elevation
    # m = moisture
    # taken from http://www.redblobgames.com/maps/terrain-from-noise/
    if (e < 0.1):
        return 0 # OCEAN

    if (e < 0.12):
        return 1 # BEACH

    if (e < 0.3):
        if (m < 0.16):
            return 2 # DESERT
        if (m < 0.33):
            return 3 # GRASSLAND
        if (m < 0.66):
            return 4 # FOREST
        return 5 # RAINFOREST

    if (e < 0.6):
        if (m < 0.16):
            return 2 # DESERT
        if (m < 0.33):
            return 3 # GRASSLAND
        if (m < 0.66):
            return 4 # FOREST
        return 5 # RAINFOREST

    if (e < 0.8):
        if (m < 0.33):
            return 2 # DESERT
        if (m < 0.66):
            return 3 # GRASSLAND
        return 6 # TAIGA

    if (m < 0.2):
        return 7 # BARE
    if (m < 0.5):
        return 8 # TUNDRA
    return 9 # SNOW

###############################################################################
#       Classes                                                               #
###############################################################################

Tile = namedtuple('Tile', ['x', 'y', 'blocked', 'block_sight', 'elevation',
                           'moisture', 'biome_id'])

class Map:
    # Not designed to be directly implemented
    def __init__(self, name, width, height, con=None):
        self.name = name
        self.width = width
        self.height = height

        self.con = con
        self.objects = set()

        self.x_off = 0
        self.y_off = 0

        self._tiles = data.load_tiles(self)
        self._grid = deque()

    @property
    def grid(self):
        return self._grid

    @property
    def tiles(self):
        return self._tiles

    def dump(self):
        data.dump(self.tiles,data.TILE_DATA_FILE.format(self.name))

    def draw(self):
        assert self.con is not None, 'There must be a console to draw to!'

        color = colors['dark_wall']

        for y,row in enumerate(self.grid):
            for x,tile in enumerate(row):
                elev = (0xFF * tile.elevation) // 1
                moist = (0xFF * tile.moisture) // 1
                bgcolor = moist + moist*0x100 + elev*0x10000
                self.con.draw_char(x, y, char=None, bg=bgcolor)

        for object in self.objects:
            object.draw()

    def clear(self):
        for object in self.objects:
            object.clear()

    def __str__(self):
        return '\n'.join([' '.join(['%.2f' % tile.elevation
                                   for tile in row]) for row in self.grid])

    def at(self, x, y):
        return self.grid[y-self.y_off][x-self.x_off]
    def set_con(self,con):
        self.con=con

    def add_object(self, object):
        self.objects.add(object)
    def remove_object(self, object):
        self.objects.remove(object)
    def discard_object(self, object):
        self.objects.discard(object)
    def pop_object(self):
        return self.objects.pop()
    def contains(self, object):
        return object in self.objects

class WorldMap(Map):
    def __init__(self, name, width, height, con=None, seed='seed'):
        super().__init__(name, width, height, con)
        seed = abs(hash(seed))
        self.elevation_gen = noise.Noise(mode='TURBULENCE', lacunarity=3.0,
                                         hurst=0.2, octaves=8, seed=seed)
        self.moisture_gen = noise.Noise(mode='TURBULENCE', lacunarity=3.0,
                                        hurst=0.2, octaves=8, seed=seed//2)

        for x in range(self.x_off, self.x_off + width):
            self.grid.append(deque())
            for y in range(self.y_off, self.y_off + height):
                self.tiles[x,y] = self.create_tile(x,y)
                self.grid[-1].append(self.tiles[x,y])

    def create_tile(self, x, y):
        # check if this tile has already been created
        if (x,y) in self.tiles:
            return self.tiles[x,y]

        # if not, generate and return the tile
        e = self.elevation_gen.get_point(x/1024,y/1024)
        m = self.moisture_gen.get_point(x/1024,y/1024)
        biome_id = get_biome(e,m)
        return Tile(x=x, y=y, blocked=biome_id==-1, block_sight=False,
                    elevation=e, moisture=m, biome_id=biome_id)


    def pan(self, dx=0, dy=0):
        if not dx and not dy:
            return
        if dx > 0: # going right
            x = self.x_off + self.width - 1
            y = self.y_off
            for row in self.grid:
                # remove the furthest left tile from each row and add to tiles
                tile = row.popleft()
                self.tiles[tile.x,tile.y] = tile
                # add a new tile to the far right of each row
                row.append(self.create_tile(x,y))
                y += 1
            self.x_off += 1
            self.pan(dx=dx-1)

        elif dx < 0: # going left
            x = self.x_off
            y = self.y_off
            for row in self.grid:
                # remove the furthest right tile from each row and add to tiles
                tile = row.pop()
                self.tiles[tile.x,tile.y] = tile
                # add a new tile to the far left of each row
                row.appendleft(self.create_tile(x,y))
                y += 1
            self.x_off -= 1
            self.pan(dx=dx+1)

        if dy > 0: # going down
            # remove the entire top row and add each tile to tiles
            for tile in self.grid.popleft():
                self.tiles[tile.x,tile.y] = tile
            # create a new row and append it to the bottom
            self.grid.append(deque())
            y = self.y_off + self.height - 1
            for x in range(self.x_off, self.x_off + self.width):
                self.grid[-1].append(self.create_tile(x,y))

            self.y_off += 1
            self.pan(dy=dy-1)

        elif dy < 0: # going up
            # remove the entire bottom row and add each tile to tiles
            for tile in self.grid.pop():
                self.tiles[tile.x,tile.y] = tile
            # create a new row and append it to the bottom
            self.grid.appendleft(deque())
            y = self.y_off - 1
            for x in range(self.x_off, self.x_off + self.width):
                self.grid[0].append(self.create_tile(x,y))

            self.y_off -= 1
            self.pan(dy=dy+1)
