#!/usr/bin/env python3

import tdl

##########################
# Classes                #
##########################

class Monster:
    def __init__(self,x,y,char='@',color=0xFFFFFF):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx, dy):
        if dx:
            self.x += dx
        if dy:
            self.y += dy

    def attempt_to_move(self, dx, dy):
        self.move(dx, dy)

    def draw(self,console):
        console.draw_char(self.x, self.y, self.char, bg=None, fg=self.color)


##########################
# Constants              #
##########################

# size of window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# maximum fps
FPS_LIMIT = 60

# names of data files
COLOR_DATA_FILE = 'colors.dat'
KEYBIND_DATA_FILE = 'keybinds.dat'

# read in colors
colors = {}
colors['WHITE'] = 0xFFFFFF

# read in keybinds
keybinds = [{} for _ in range(8)]
try:
    with open(KEYBIND_DATA_FILE) as f:
        for l in f:
            if l[0] not in '#\n':
                event_name = l.split('=')[0].strip()
                keybind_values = l.split('=')[1]
                for binding in keybind_values.split(','):
                    modifier = 0
                    prefix = binding[:3]
                    if '+' in prefix:
                        prefix = prefix.replace('+','')
                        modifier += 1
                    if '!' in prefix:
                        prefix = prefix.replace('!','')
                        modifier += 2
                    if '^' in prefix:
                        prefix = prefix.replace('^','')
                        modifier += 4
                    binding = prefix + binding[3:]
                    keybinds[modifier][binding.strip()] = event_name
except:
    print('Error reading in keybinds.')

##########################
# Functions              #
##########################

def exit_game():
    exit()

def toggle_fullscreen():
    tdl.set_fullscreen(not tdl.get_fullscreen())

##########################
# Pre-Handling Inits     #
##########################

player = Monster(1,1)

##########################
# Event Handling         #
##########################

EVENTS = {}

# Player Actions
EVENTS['move_right'] = lambda player=player:player.attempt_to_move(1,0)
EVENTS['move_left'] = lambda player=player:player.attempt_to_move(-1,0)
EVENTS['move_up'] = lambda player=player:player.attempt_to_move(0,-1)
EVENTS['move_down'] = lambda player=player:player.attempt_to_move(0,1)

# Game Actions
EVENTS['toggle_fullscreen'] = toggle_fullscreen
EVENTS['exit_game'] = exit_game


def handle_keys():
    global player

    user_input = tdl.event.key_wait()

    # modifier is based on keys currently held down
    modifier = 4 * user_input.control + 2 * user_input.alt + user_input.shift
    
    print(user_input.keychar)
    # check to see if current modifier + key is in the keybind database
    if user_input.keychar in keybinds[modifier]:
        event_name = keybinds[modifier][user_input.keychar]
    else:
        return

    try:
        EVENTS[event_name]()
    except KeyError:
        print('Bad event code. Did you mess with keybinds.dat?')
        exit_game()

##########################
# Game Logic             #
##########################

tdl.set_font('arial12x12.png', greyscale=True, altLayout=True)
console = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Roguelike", fullscreen=False)

while not tdl.event.is_window_closed():
    console.draw_char(player.x,player.y,' ',bg = None)
    handle_keys()
    player.draw(console)
    tdl.flush()
