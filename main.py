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

    def move(self, dx, dy):
        if (dx and 0 <= self.x+dx and self.x+dx < self.map.width and
                not self.map.at(self.x+dx, self.y).blocked):
            self.x += dx
            advance()
        if (dy and 0 <= self.y+dy and self.y+dy < self.map.height and
                not self.map.at(self.x, self.y+dy).blocked):
            self.y += dy
            advance()

        #print(self.x, self.y, self.map.at(self.x, self.y))

    def clear(self):
        if self.map is current_map:
            con.draw_char(self.x, self.y, ' ', bg=None)

    def draw(self):
        if self.map is current_map:
            con.draw_char(self.x, self.y, self.char, bg=None, fg=self.color)

class Player(VisibleObject):
    def move(self, dx, dy):
        super().move(dx, dy)
        camera.snap()

    def attempt_to_move(self, dx, dy):
        self.move(dx, dy)

class Camera:
    def __init__(self, x=0, y=0, following=None):
        """
        Args:
            x: optional, x position of camera
            y: optional, y position of camera
            following: what camera snaps to by default
        """
        if following:
            self.following = following
            self.x = 0
            self.y = 0
            self.snap()

        else:
            self.following = None
            self.x = x
            self.y = y

    def snap(self,target=None):
        if target is None:
            target = self.following

        assert target, 'snap() called without a target for camera'

        if CENTER_X <= target.x and target.x <= target.map.width - DRAWN_WIDTH + CENTER_X:
            self.x = target.x - CENTER_X
        if CENTER_Y <= target.y and target.y <= target.map.height - DRAWN_HEIGHT + CENTER_Y:
            self.y = target.y - CENTER_Y

###############################################################################
#       Functions                                                                   #
###############################################################################

def exit_game():
    exit()

def toggle_fullscreen():
    tdl.set_fullscreen(not tdl.get_fullscreen())

def advance():
    global turn_number
    # a turn has been taken successfully
    turn_number += 1

###############################################################################
#       Pre-Handling Initialization                                           #
###############################################################################

current_map = mapgen.Map(100,100,seed='test',type='main')
print(current_map)

player = Player(1, 1, current_map,'@',colors['player'])
camera = Camera(following=player)

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
current_map.con = con

turn_number = 0

while not tdl.event.is_window_closed():
    #draw all objects
    current_map.draw()

    root.blit(current_map.con, srcX=camera.x, srcY=camera.y,
              width=DRAWN_WIDTH, height=DRAWN_HEIGHT)

    tdl.flush()

    #clear all objects before the next movement
    current_map.clear()

    handle_key_events()
