#!/usr/bin/env python3

import tdl
import random
from opensimplex import OpenSimplex
from math import sin, cos

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


def get_elevation(x,y):
    e = noise(x+0.5, y+0.5, octaves=6, persistence=1.5, lacunarity=0.7,
                repeatx=1024, repeaty=1024)
    return  ((e+1)/2)

def get_moisture(x,y):
    m = noise(x+0.5, y+0.5, octaves=3, persistence=0.5, lacunarity=2.0,
                 repeatx=0x10000,repeaty=0x10000)
    return ((m+1)/2) ** 2

def get_biome(e,m):
    return 1
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
                 repeatx=1024, repeaty=1024, pow=1):
        self.generator = OpenSimplex(hash(seed))
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.repeatx = repeatx
        self.repeaty = repeaty
        self.pow = pow

    def get(self,x,y):
        # seamless noise algorithm taken from:
        # https://www.gamedev.net/blog/33/entry-2138456-seamless-noise/

        s = x / self.repeatx
        t = y / self.repeaty

        x1, y1 = 0, 0
        x2, y2 = 1, 1

        dx = x2 - x1
        dy = y2 - y1

        # sum of the noise
        total = 0
        # frequency increase from successive octaves, grows based on lacunarity
        d = 0.1
        # dampening (multiplying) factor, shrinks based on persistence
        m = 1

        for octave in range(self.octaves):
            nx = x + cos(s*2*pi)*dx/(2*pi)
            ny = y + cos(t*2*pi)*dy/(2*pi)
            nz = x + sin(s*2*pi)*dx/(2*pi)
            nw = y + sin(t*2*pi)*dy/(2*pi)

            total += self.generator.noise4d(d*nx,d*ny,d*nz,d*nw) * m
            m *= self.persistence
            d *= self.lacunarity

        if (total + 1) / 2 < 0:
            return 0
        return ((total + 1) / 2) ** self.pow


class Tile:
    def __init__(self, blocked=False, block_sight=None,
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

    def __str__(self):
        return 'Elevation: %.4f\nBiome: %s' % ([self.biome_id])

    def __eq__(self, other):
        if type(other) is not Tile:
            return False
        return self.id == other.id
    def __ne__(self, other):
        return not self == other

class Map:
    def __init__(self, width, height, con=None, seed='seed', type=None):
        self.con = con
        self.objects = set()

        self.width = width
        self.height = height

        #if seed is not None:
        #    random.seed(seed)

        if type is None:
            self.grid = [[ Tile(False) if random.randrange(50) else Tile(True)
                          for y in range(height) ]
                            for x in range(width) ]
        elif type == 'main':
            self.elevation_gen = NoiseGenerator(seed[len(seed)//2:], octaves=8,
                                                persistence=2.0, lacunarity=0.1,
                                                repeatx=0x10000,repeaty=0x10000,
                                                pow=0.5)
            #self.moisture_gen = NoiseGenerator(seed[:len(seed)//2], octaves=3,
            #                                    persistence=0.5, lacunarity=2.0,
            #                                    repeatx=0x10000,repeaty=0x10000,
            #                                    pow=3)
            self.grid = []
            for x in range(width):
                self.grid.append([])
                for y in range(height):
                    e = self.elevation_gen.get(x,y)
                    m = 0#self.moisture_gen.get(x,y)
                    biome_id = get_biome(e,m)
                    self.grid[-1].append(Tile(blocked=biome_id==0,
                                              block_sight=False,
                                              elevation=e,
                                              moisture=m,
                                              biome_id=biome_id))


    def __getitem__(self, index):
        # sorta hacky -- returns the row of Tiles corresponding to
        # the given index
        return self.grid[index]

    def draw(self):
        assert self.con is not None, 'There must be a console to draw to!'

        color = colors['dark_wall']

        for y,row in enumerate(self.grid):
            for x,tile in enumerate(row):
                elev = (0xFF * tile.elevation) // 2
                moist = (0xFF * tile.moisture) // 2
                bgcolor = elev + elev*0x100 + elev*0x10000
                self.con.draw_char(x, y, char=None, bg=bgcolor)

        for object in self.objects:
            object.draw()

    def clear(self):
        for object in self.objects:
            object.clear()

    def __str__(self):
        return '\n'.join([' '.join(['%.2f'%tile.elevation
                                   for tile in row]) for row in self.grid])

    def update_position(self, dx, dy):


    def at(self, x, y):
        return self.grid[y][x]

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
