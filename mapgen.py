#!/usr/bin/env python3

import tdl
import random
from noise import pnoise2
from math import sin, cos
from collections import deque

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

class NoiseGenerator():
    def __init__(self, seed=0, octaves=1, persistence=0.5, lacunarity=2.0,
                 repeatx=1024, repeaty=1024, exponent=1, div=1024):
        self.seed = seed
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.repeatx = repeatx
        self.repeaty = repeaty
        self.exponent = exponent
        #factor to divide initial values by
        self.div = div

    def get(self,x,y):
        e = pnoise2(x/self.div, y/self.div,
                    octaves=self.octaves,
                    persistence=self.persistence,
                    lacunarity=self.lacunarity,
                    repeatx=self.repeatx,
                    repeaty=self.repeaty)
        return  ((e+1)/2) ** self.exponent


class Tile:
    def __init__(self, blocked=False, block_sight=False,
                 elevation=0.5, moisture=0.5, biome_id=0):
        self.blocked = blocked

        #by default, blocked tiles block sight, clear ones don't
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight

        self.elevation = elevation
        self.moisture = moisture
        self.biome_id = biome_id

    def __bool__(self):
        return self.block_sight

    def __repr__(self):
        return 'Tile({}, {}, {}, {}, {})'.format(self.blocked, self.block_sight,
                                                 self.elevation, self.moisture,
                                                 self.biome_id)
    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        if type(other) is not Tile:
            return False
        return self.id == other.id
    def __ne__(self, other):
        return not self == other

class Map:
    # ABSTRACT CLASS -- DO NOT IMPLEMENT!!!
    def __init__(self, width, height, con=None):
        self.width = width
        self.height = height

        self.con = con
        self.objects = set()

        self.x_off = 0
        self.y_off = 0

    def __getitem__(self, index):
        # sorta hacky -- returns the row of Tiles corresponding to
        # the given index
        return self.grid[index]

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
        return '\n'.join([' '.join(['%.2f'%tile.elevation
                                   for tile in row]) for row in self.grid])

    def at(self, x, y):
        return self.grid[y][x]
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
    def __init__(self, width, height, con=None, seed='seed'):
        super().__init__(width,height,con)

        self.elevation_gen = NoiseGenerator(seed[len(seed)//2:], octaves=8,
                                            persistence=9.0, lacunarity=1.3,
                                            repeatx=0x10000,repeaty=0x10000,
                                            exponent=3, div=0x1000)
        self.moisture_gen = NoiseGenerator(seed[:len(seed)//2], octaves=3,
                                           persistence=0.5, lacunarity=2.0,
                                           repeatx=0x10000,repeaty=0x10000,
                                           exponent=3, div=0x1000)

        self.grid = deque()

        for x in range(self.x_off, self.x_off + width):
            self.grid.append(deque())
            for y in range(self.y_off, self.y_off + height):
                e = self.elevation_gen.get(x,y)
                m = self.moisture_gen.get(x,y)
                biome_id = get_biome(e,m)
                self.grid[-1].append(Tile(blocked=biome_id==0, elevation=e,
                                          moisture=m, biome_id=biome_id))

    def pan(self, dx=0, dy=0):
        if not dx and not dy:
            return
        print('pan {} {}'.format(dx, dy))
        if dx > 0: # going right
            x = self.x_off + self.width - 1
            for y,row in enumerate(self.grid):
                row.popleft()
                y += self.y_off
                e = self.elevation_gen.get(x,y)
                m = self.moisture_gen.get(x,y)
                biome_id = get_biome(e,m)
                row.append(Tile(blocked=biome_id==0, elevation=e,
                                moisture=m, biome_id=biome_id))
            self.x_off += 1
            self.pan(dx=dx-1)

        elif dx < 0: # going left
            x = self.x_off
            for y,row in enumerate(self.grid):
                row.pop()
                y += self.y_off
                e = self.elevation_gen.get(x,y)
                m = self.moisture_gen.get(x,y)
                biome_id = get_biome(e,m)
                row.appendleft(Tile(blocked=biome_id==0, elevation=e,
                                    moisture=m, biome_id=biome_id))
            self.x_off -= 1
            self.pan(dx=dx+1)

        if dy > 0: # going down
            self.grid.pop()
            new_row = deque()
            y = self.y_off + self.height - 1
            for x in range(self.x_off, self.x_off + self.width):
                e = self.elevation_gen.get(x,y)
                m = self.moisture_gen.get(x,y)
                biome_id = get_biome(e,m)
                new_row.append(Tile(blocked=biome_id==0, elevation=e,
                                    moisture=m, biome_id=biome_id))
            self.grid.appendleft(new_row)
            self.y_off += 1
            self.pan(dy=dy-1)

        elif dy < 0: # going up
            self.grid.popleft()
            new_row = deque()
            y = self.y_off - 1
            for x in range(self.x_off, self.x_off + self.width):
                e = self.elevation_gen.get(x,y)
                m = self.moisture_gen.get(x,y)
                biome_id = get_biome(e,m)
                new_row.append(Tile(blocked=biome_id==0, elevation=e,
                                    moisture=m, biome_id=biome_id))
            self.grid.append(new_row)
            self.y_off -= 1
            self.pan(dy=dy+1)
