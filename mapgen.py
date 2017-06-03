#!/usr/bin/env python3

import tdl
import random
from data import colors

###############################################################################
#       Constants                                                             #
###############################################################################

# names of Tiles
TILE_NAMES = ['dark_ground','dark_wall']

###############################################################################
#       Classes                                                               #
###############################################################################


class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        #by default, blocked tiles block sight, clear ones don't
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight

        self.id = 1 if blocked else 0

    def __bool__(self):
        return self.block_sight

    def __str__(self):
        return TILE_NAMES[self.id]

    def __eq__(self,other):
        if type(other) is not Tile:
            return False
        return self.id == other.id
    def __ne__(self,other):
        return not self == other

class Map:
    def __init__(self, width, height, con=None, seed=None, type=None):
        self.width = width
        self.height = height
        self.con = con

        if seed is not None:
            random.seed(seed)

        if type is None:
            self.grid = [[ Tile(False) if random.randrange(50) else Tile(True)
                          for y in range(height) ]
                            for x in range(width) ]
        elif type == 'forest':
            pass



    def __getitem__(self, index):
        # sorta hacky -- returns the row of Tiles corresponding to
        # the given index
        return self.grid[index]

    def draw(self):
        assert self.con is not None, 'There must be a console to draw to!'

        last_tile = None
        for y,row in enumerate(self.grid):
            for x,tile in enumerate(row):
                if tile != last_tile:
                    color = colors[TILE_NAMES[tile.id]]
                self.con.draw_char(x,y,' ',bg=color,fg=None)
                last_tile = tile

    def __str__(self):
        return_str = ''
        for row in self.grid:
            row_str = ''
            for tile in row:
                row_str += str(tile.id) + ' '
            return_str += row_str[:-1] + '\n'
        return return_str[:-1]

    def at(self,x,y):
        return self.grid[y][x]
