#!/usr/bin/env python3

import tdl
import heapq

import mapgen
from data import colors, keybinds

###############################################################################
#       Constants                                                             #
###############################################################################

# size of window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# size of actual drawn area
DRAWN_WIDTH = 60
DRAWN_HEIGHT = 45

# center of the drawn area (where player generally will sit)
CENTER_X = DRAWN_WIDTH // 2
CENTER_Y = DRAWN_HEIGHT // 2

# maximum fps
FPS_LIMIT = 60

###############################################################################
#       Classes                                                               #
###############################################################################

class VisibleObject:
    def __init__(self, x, y, map, char='@', color=0xFFFFFF):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.map = map

    def move_x(self, dx):
        if (dx and self.map.x_off <= self.x+dx
                and self.x+dx < self.map.width + self.map.x_off
                and not self.map.at(self.x+dx, self.y).blocked):
            self.x += dx
            return True
        return False

    def move_y(self, dy):
        if ( dy and self.map.y_off <= self.y+dy
                and self.y+dy < self.map.height + self.map.y_off
                and not self.map.at(self.x, self.y+dy).blocked):
            self.y += dy
            return True
        return False

    def move(self, dx, dy):
        return (self.move_x(dx) | self.move_y(dy))

    def clear(self):
        self.map.con.draw_char(self.x-self.map.x_off, self.y-self.map.y_off,
                               ' ', bg=None)

    def draw(self):
        self.map.con.draw_char(self.x-self.map.x_off, self.y-self.map.y_off,
                               self.char, bg=None, fg=self.color)

class Player(VisibleObject):
    def move(self, dx, dy):
        if dx:
            if super().move_x(dx):
                self.map.pan(dx=dx)
                advance(abs(dx))
        if dy:
            if super().move_y(dy):
                self.map.pan(dy=dy)
                advance(abs(dy))

        #print(self.map)

    def attempt_to_move(self, dx, dy):
        self.move(dx, dy)

###############################################################################
#       Functions                                                                   #
###############################################################################

def exit_game():
    current_map.dump()
    exit()

def toggle_fullscreen():
    tdl.set_fullscreen(not tdl.get_fullscreen())

def advance(delta=1):
    global turn_number
    # a turn has been taken successfully
    turn_number += delta

###############################################################################
#       Pre-Handling Initialization                                           #
###############################################################################

current_map = mapgen.WorldMap('main', DRAWN_HEIGHT*3, DRAWN_WIDTH*3,
                              seed='test')
#print(current_map)

spawn_x, spawn_y = (CENTER_X, CENTER_Y)
player = Player(spawn_x, spawn_y, current_map, '@', colors['player'])

current_map.add_object(player)

###############################################################################
#       Event Handling                                                        #
###############################################################################

key_events = {
# Player Movement
'move_right'        : lambda player=player:player.attempt_to_move(1,0),
'move_left'         : lambda player=player:player.attempt_to_move(-1,0),
'move_up'           : lambda player=player:player.attempt_to_move(0,-1),
'move_down'         : lambda player=player:player.attempt_to_move(0,1),

'move_down_right'   : lambda player=player:player.attempt_to_move(1,1),
'move_up_right'     : lambda player=player:player.attempt_to_move(1,-1),
'move_down_left'    : lambda player=player:player.attempt_to_move(-1,1),
'move_up_left'      : lambda player=player:player.attempt_to_move(-1,-1),

# Game Actions
'toggle_fullscreen' : toggle_fullscreen,
'exit_game'         : exit_game
}


def handle_key_events():
    user_input = tdl.event.key_wait()

    # modifier is 3 bits, based on keys currently held down
    modifier = 4 * user_input.control + 2 * user_input.alt + user_input.shift

    # check to see if current modifier + key is in the keybind database
    if user_input.keychar in keybinds[modifier]:
        event_name = keybinds[modifier][user_input.keychar]
    else:
        return

    # attempt to execute the corresponding function
    try:
        key_events[event_name]()
    except KeyError:
        print('Bad event code. Did you mess with keybinds.dat?')
        exit_game()

###############################################################################
#       Game Logic                                                            #
###############################################################################

tdl.set_font('arial12x12.png', greyscale=True, altLayout=True)
tdl.setFPS(FPS_LIMIT)

root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT,
                title="Roguelike", fullscreen=False)
con = tdl.Console(current_map.width,current_map.height)
current_map.set_con(con)

turn_number = 0

while not tdl.event.is_window_closed():
    #draw all objects
    current_map.draw()

    camera_x = spawn_x - CENTER_X
    camera_y = spawn_y - CENTER_Y

    print(current_map)
    print('Player Loc: ({p.x},{p.y})'.format(p=player))
    print('Player Loc: ({},{})'.format(player.x - current_map.x_off,
                                       player.y - current_map.y_off))
    print('Camera: ({},{})'.format(camera_x,camera_y))
    print('Map Offset: ({},{})'.format(current_map.x_off, current_map.y_off))

    root.blit(current_map.con, srcX=camera_x, srcY=camera_y,
              width=DRAWN_WIDTH, height=DRAWN_HEIGHT)

    tdl.flush()

    #clear all objects before the next movement
    current_map.clear()

    handle_key_events()
