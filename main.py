'''
puzzle
'''
import random
import math

import kivy
kivy.require('1.8.0')

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.label import Label
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, ReferenceListProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.vector import Vector
from kivy.animation import Animation


from helpers import white, grey, black, clear, red, green, blue, yellow, purple, game_bg_color, menu_bg_color

import levels

game_id = 'puzzle kingdom v0.1'

'''
Powers Brainstorming
====================
Fortress: gain military strength to attack neighboring tile
Castle: political power used to sway tiles to your side
Abbey: use religious power to bless or curse other tiles
Tradeship: convert one neighboring resource to any other at 2 for 1 ratio
Village: workforce can be used to relocate tiles (number influence == maximum power of tile that can be moved)
Mine: provide one resource type of neighboring tiles per point of mine power
Farm: food -- not sure. Add one power to every tile for n turns

Tiles not currently supported
Workshop/Mason: builds other buildings (power determines which building)
'''


def load_images():
    terrain_dict={}
    terrain_dict['p'] = 'tiles/terrain_plain.png'
    terrain_dict['f'] = 'tiles/terrain_forest.png'
    terrain_dict['m'] = 'tiles/terrain_mountain.png'
    terrain_dict['w'] = 'tiles/terrain_water.png'
    terrain_dict['1'] = 'tiles/terrain_water_edge_n.png'
    terrain_dict['2'] = 'tiles/terrain_water_edge_ne.png'
    terrain_dict['3'] = 'tiles/terrain_water_edge_se.png'
    terrain_dict['4'] = 'tiles/terrain_water_edge_s.png'
    terrain_dict['5'] = 'tiles/terrain_water_edge_sw.png'
    terrain_dict['6'] = 'tiles/terrain_water_edge_nw.png'
    terrain_dict['C'] = 'tiles/tile_castle.png'
    terrain_dict['V'] = 'tiles/tile_village.png'
    terrain_dict['A'] = 'tiles/tile_abbey.png'
    terrain_dict['F'] = 'tiles/tile_farm.png'
    terrain_dict['M'] = 'tiles/tile_mine.png'
    terrain_dict['S'] = 'tiles/tile_stronghold.png'
    terrain_dict['T'] = 'tiles/tile_tradeship.png'
    return terrain_dict


def color_average(a, b, a_wgt = 0.0):
    return [a_wgt*x+(1-a_wgt)*y for x,y in zip(a,b)]

class Tile(Image):
    code = ''
    value = NumericProperty()
    selected = BooleanProperty(False)
    hex_pos_row = NumericProperty()
    hex_pos_col = NumericProperty()
    hex_pos = ReferenceListProperty(hex_pos_col, hex_pos_row)
    tile_color = ListProperty()
    text_color = ListProperty()
    score = NumericProperty(0)
    w_label = ObjectProperty()

    def __init__(self, board, player = None,
             **kwargs):
        super(Tile,self).__init__(**kwargs)
        self.board = board
        self.player = player
        self.hex_pos = [-1,-1] #start off board
        self.bind(selected = self.on_selected)
        self.source = self.board.terrain_images[self.code]
        self.allow_stretch = True

    def place(self, hex_pos, center_pos, player):
        if self.selected:
            self.hex_pos = hex_pos
            a = Animation(center_x = center_pos[0], center_y = center_pos[1], duration = 0.1)
            a.start(self)

    def on_touch_down(self, touch):
        if self.pos[0]<touch.pos[0]<self.pos[0]+self.size[0] and \
            self.pos[1]<touch.pos[1]<self.pos[1]+self.size[1]:
            if self.board.on_touch_down_tile(self, touch):
                return True

    def on_selected(self, obj, value):
        if value == True:
            a = Animation(x = self.board.select_pos[0], y = self.board.select_pos[1], duration = 0.1)
            a.start(self)
        if value == False:
            x = self.board.selectable_tiles.index(self)
            pos = (0 * (self.board.hex_side*2 + 0.01*self.board.size[0]),
                     self.board.size[1] - (1 + x) * (self.board.hex_side*2 + 0.01*self.board.size[0]))
            a = Animation(x = pos[0], y = pos[1], duration = 0.1)
            a.start(self)

class Castle(Tile):
    code = 'C'
    score_tiles = {'C': -1, 'V': 1, 'S': 1, 'M': -1, 'T': 1, 'A': 1, 'F': -1, '': 0  }
    score_terrain = {'p': 1, 'f': 1, 'm': 0, 'w': None} #plain, forest, mountain, water
    tile_color = purple
    text_color = white

class Village(Tile):
    code = 'V'
    score_tiles = {'C': 1, 'V': -1, 'S': 1, 'M': 1, 'T': 1, 'A': 1, 'F': 1, '': 0 }
    score_terrain = {'p': 1, 'f': 1, 'm': 0, 'w': None} #plain, forest, mountain, water
    tile_color = yellow
    text_color = white

class Stronghold(Tile):
    code = 'S'
    score_tiles = {'C': -1, 'V': 1, 'S': -1, 'M': 1, 'T': 1, 'A': 1, 'F': 1, '': 0  }
    score_terrain = {'p': 1, 'f': 0,'m': 1, 'w': None} #plain, forest, mountain, water
    tile_color = red
    text_color = white

class Mine(Tile):
    code = 'M'
    score_tiles = {'C': -1, 'V': 1, 'S': -1, 'M': -1, 'T': 1, 'A': 1, 'F': 1, '': 0  }
    score_terrain = {'p': 1, 'f': 0, 'm': 2, 'w': None} #plain, forest, mountain, water
    tile_color = grey
    text_color = white

class Tradeship(Tile):
    code = 'T'
    score_tiles = {'C': 1, 'V': 1, 'S': -1, 'M': 1, 'T': -1, 'A': 1, 'F': 1, '': 0 }
    score_terrain = {'p': None, 'f': None, 'm': None, 'w': 2} #plain, forest, mountain, water
    tile_color = [0.4,0.2,0.2,1.0]
    text_color = white

class Abbey(Tile):
    code = 'A'
    score_tiles = {'C': -1, 'V': 1, 'S': -1, 'M': -1, 'T': 1, 'A': -1, 'F': 1, '': 0  }
    score_terrain = {'p': 1, 'f': 1, 'm': 1, 'w': None} #plain, forest, mountain, water
    tile_color = [0.7, 0.4, 0.4, 1.0]
    text_color = white

class Farm(Tile):
    code = 'F'
    score_tiles = {'C': -1, 'V': 1, 'S': -1, 'M': -1, 'T': 1, 'A': 1, 'F': -1, '': 0.5 }
    score_terrain = {'p': 2, 'f': 1,'m': None, 'w': None} #plain, forest, mountain, water
    tile_color = [0.2,0.5,0.2,1.0]
    text_color = white

tile_dict = dict([(str(c.code), c) for c in Tile.__subclasses__()])

class TerrainHex(Image):
    code = StringProperty()
    hex_width = NumericProperty()
    hex_height = NumericProperty()
    hex_len = NumericProperty()
    hex_pos_x = NumericProperty()
    hex_pos_y = NumericProperty()
    hex_pos = ReferenceListProperty(hex_pos_x, hex_pos_y)
    texture = ObjectProperty()

    def __init__(self, board, **kwargs):
        super(TerrainHex, self).__init__(**kwargs)
        self.board = board
        self.tile = None
        self.texture = None
        self.source = self.board.terrain_images[self.code]
        self.allow_stretch = True

    def on_touch_down(self, touch):
        if (touch.pos[0] - self.center_x)**2 + (touch.pos[1] - self.center_y)**2 < (self.hex_height/2)**2:
            self.board.on_touch_down_terrain(self, touch)

lightgreen = [0.5, 1.0, 0.5, 1.0]


class Plain(TerrainHex):
    code = StringProperty('p')

class Forest(TerrainHex):
    code = StringProperty('f')

class Mountain(TerrainHex):
    code = StringProperty('m')

class Water(TerrainHex):
    code = StringProperty('w')

terrain_class = {'p': Plain, 'f': Forest, 'm': Mountain, 'w': Water}

class StatusLabel(Label):
    bg_color = ListProperty()

class Board(FloatLayout):
    board_hex_count = NumericProperty()
    board_width = NumericProperty()
    board_height = NumericProperty()
    hex_width = NumericProperty()
    hex_side = NumericProperty()
    hex_height = NumericProperty()

    def __init__(self):
        super(Board,self).__init__()
        self.terrain_images = load_images()
        self.bind(size = self.size_changed)
        self.terrain = None #the set of terrain tiles on the board
        self.tiles = [] #list of undrawn tiles that will be drawn over the course of the game
        self.selectable_tiles = [] #list of tiles available for players to select and place
        self.tile_stack = [] #list of tiles available for players to select and place
        self.selected_tile = None #the tile that has been selected but not placed by a player
        self.active_player = -1 #player whose turn it is
        self.players = [] #the list of players (including AI)
        self.scoreboard = ScoreBoard() #widget that displays the player scores
        self.add_widget(self.scoreboard)
        self.game_over = False
        self.w_state_label = StatusLabel(text = '', bg_color = clear, color = white, pos_hint ={'right': 0.99, 'y': 0.01})
        self.add_widget(self.w_state_label)

    def remove_players(self):
        self.active_player = -1
        self.selected_tile = None
        for p in self.players:
            p.delete()
        self.players = []

    def clear_level(self):
        if self.terrain is not None:
            for hp in self.terrain:
                self.remove_widget(self.terrain[hp])
            self.terrain = None
        for st in self.selectable_tiles:
            self.remove_widget(st)
        self.selectable_tiles = []

    def setup_level(self, level = None):
        if level is not None:
            self.level = level
        self.terrain = {}
        i = 0
        terrainmap = self.level.map.replace('\n','').replace(' ','')
        for x in range(self.board_hex_count):
            y_height = self.board_hex_count - abs((self.board_hex_count-1)//2-x)
            for y in range(y_height):
                h = terrain_class[terrainmap[i]](self, hex_pos = (x,y))
                i += 1
                self.add_widget(h)
                self.terrain[(x,y)] = h
        self.selectable_tiles = [Castle(self), Village(self), Village(self)]
        for st in self.selectable_tiles:
            self.add_widget(st)
        self.tile_stack = [tile_dict[t](self) for t in self.level.tile_set]
        random.shuffle(self.tile_stack)
        start_tile = tile_dict[self.level.start_tile](self)
        start_tile.hex_pos = self.level.start
        self.add_widget(start_tile)
        self.terrain[self.level.start].tile = start_tile
        self.players[self.active_player].placed_tiles.append(start_tile)

    def setup_game(self, player_spec, level = None):
        self.game_over = False
        self.w_state_label.text = ''
        self.w_state_label.color = white
        self.w_state_label.bg_color = clear
        self.remove_players()
        self.clear_level()
        if len(player_spec) ==1:
            self.board_hex_count = 9
            self.tiles_count = 24
        if len(player_spec) ==2:
            self.board_hex_count = 9
            self.tiles_count = 24
        elif len(player_spec) == 3:
            self.board_hex_count = 9
            self.tiles_count = 24
        elif len(player_spec) == 4:
            self.board_hex_count = 9
            self.tiles_count = 24
        else: #5
            self.board_hex_count = 9
            self.tiles_count = 24
        for p in player_spec:
            if p.type == 0: #human
                self.players.append(Player(p.name, p.color, self))
            if p.type == 1: #computer
                self.players.append(AIPlayer(p.name, p.color, self))
            if p.type == 2: #network
                self.players.append(NetworkPlayer(p.name, p.color, self))
        self.setup_level(level)

    def start_game(self):
        self.next_player()

    def next_player(self):
        if self.active_player >= 0:
            self.players[self.active_player].end_turn()
            if len(self.selectable_tiles) == 0:
                self.show_game_over()
                return
        self.active_player +=1
        if self.active_player >= len(self.players):
            self.active_player = 0
        p = self.players[self.active_player]
        p.start_turn()
        if p.local_control:
            self.w_state_label.text = 'Select tile'
            self.w_state_label.color = color_average(white, p.color)
        else:
            self.w_state_label.text = ''
            self.w_state_label.color = white

    def show_game_over(self):
        scores = [p.score_marker.score for p in self.players]
        hi_score = max(scores)
        winners = [self.players[z] for (z,s) in zip(range(len(self.players)), scores) if s == hi_score]
        self.game_over = True
        if len(self.players) == 1:
            rating = 'you bankrupted the kingdom!'
            if hi_score>40:
                rating = 'time to find another job'
            if hi_score>60:
                rating = 'the people are happy'
            if hi_score>80:
                rating = 'the people are joyous!'
            if hi_score>90:
                rating = 'welcome to the history books'
            if hi_score>100:
                rating = 'hail to the king!'
            self.w_state_label.color = color_average(white, winners[0].color)
            self.w_state_label.text = 'Game over - %s'%(rating,)
        elif len(winners) == 1:
            self.w_state_label.color = color_average(white, winners[0].color)
            self.w_state_label.text = 'Game over - %s wins'%(winners[0].name)
        else:
            self.w_state_label.color = white
            self.w_state_label.text = 'Game over - draw'

    def draw_new_tile(self):
        if len(self.tile_stack)==0:
            return
        t = self.tile_stack.pop()

        self.selectable_tiles.append(t)
        self.add_widget(t)
        for x, st in zip(range(len(self.selectable_tiles)), self.selectable_tiles):
            st.pos = (0 * (self.hex_side*2 + 0.01*self.size[0]),
                     self.size[1] - (1 + x) * (self.hex_side*2 + 0.01*self.size[0]))
            st.size = [self.hex_side*2, self.hex_side*2]

    def size_changed(self,*args):
        self.hex_side = min(self.size[0]/(1.5 * self.board_hex_count + 1), 0.95*self.size[1]/(self.board_hex_count * 3**0.5))
        self.hex_width = self.hex_side*2
        self.hex_height = self.hex_side * (3**0.5)
        self.board_height = self.hex_height * self.board_hex_count
        self.board_width = self.hex_side * (1.5 * self.board_hex_count + 1)
        if self.terrain is not None:
            for x in range(self.board_hex_count):
                y_height = self.board_hex_count - abs((self.board_hex_count-1)//2-x)
                for y in range(y_height):
                    center = self.pixel_pos((x,y))
                    size = self.hex_width, self.hex_width
                    self.terrain[(x,y)].size = size
                    self.terrain[(x,y)].center = center
            self.select_pos = [3*(self.hex_side*2 + 0.01*self.size[0]) , self.size[1] - self.hex_side*2 - 0.01*self.size[0]]
        for p in self.players:
            p.board_resize(self.pos, self.size, self.hex_side)
        self.scoreboard.size = (60*len(self.players)+0.01*self.size[0]*(len(self.players)-1), 80)
        self.scoreboard.right = 0.99 * self.size[0]
        self.scoreboard.top = self.size[1] - 0.01*self.size[0]
        self.scoreboard.update_size(self.size)
        for x, st in zip(range(len(self.selectable_tiles)), self.selectable_tiles):
            st.pos = (0 * (self.hex_side*2 + 0.01*self.size[0]),
                     self.size[1] - (1 + x) * (self.hex_side*2 + 0.01*self.size[0]))
            st.size = [self.hex_side*2, self.hex_side*2]
        self.w_state_label.font_size = 0.04*self.size[1]

    def pixel_pos(self, hex_pos):
        '''
        returns center of hex at position represented by the tuple `hex_pos`
        '''
        return (self.center_x + self.hex_side * 1.5 * (hex_pos[0] - self.board_hex_count//2),
                self.center_y + self.hex_height * (hex_pos[1] - self.board_hex_count//2 + abs(hex_pos[0]-self.board_hex_count//2)/2.0) )

    def hex_pos(self, pixel_pos):
        '''
        returns hex position corresponding to x,y tuple in `pixel_pos`
        '''
        hpos = int((pixel_pos[0] - self.center_x)/(self.hex_side * 1.5) + self.board_hex_count//2 + 0.5)
        vpos = int((pixel_pos[1] - self.center_y)/self.hex_height + self.board_hex_count//2 - abs(hpos-self.board_hex_count//2)//2 + 0.5)
        if 0<=hpos<self.board_hex_count and 0<=vpos<self.board_hex_count:
            return hpos, vpos
        else:
            return None

    def neighbor_iter(self, hex_pos):
        y_offset_left = hex_pos[0]<=self.board_hex_count//2
        y_offset_right = hex_pos[0]>=self.board_hex_count//2
        for x,y in [(0,-1), (0,+1), (-1,-y_offset_left), (-1,+1-y_offset_left), (+1,-y_offset_right), (+1,+1-y_offset_right)]:
            try:
                yield self.terrain[(hex_pos[0]+x,hex_pos[1]+y)]
            except KeyError:
                pass

    def get_neighbor_count(self, hex_pos):
        value = 0
        for t in self.neighbor_iter(hex_pos):
            if t.tile is not None:
                value += 1
        return value

    def update_terrain_and_neighbors(self,terrain):
        pass

    def score_tile(self, terr_hex):
        tile = terr_hex.tile
        tile.score = tile.score_terrain[terr_hex.code]
        for nterr in self.neighbor_iter(tile.hex_pos):
            if nterr.tile is not None:
                tile.score += tile.score_tiles[nterr.tile.code]
        return tile.score

    def update_scores(self, terrain = None):
        if terrain is not None:
            self.score_tile(terrain)
            for terr in self.neighbor_iter(terrain.hex_pos):
                if terr.tile is not None:
                    self.score_tile(terr)
        for p in self.players:
            score = 0
            for pt in p.placed_tiles:
                score += pt.score
            p.score_marker.score = score

    def place_tile(self, terrain, server_check = True):
        '''
        called by touch handler for local player, or by AI or network
        player to place the selected tile on a terrain
        '''
        if not self.game_over and self.selected_tile is not None:
            hex_pos = terrain.hex_pos
            if self.terrain[(hex_pos[0], hex_pos[1])].tile is not None:
                return
            center_pos = self.pixel_pos(hex_pos)
            self.selected_tile.place(hex_pos, center_pos, self.players[self.active_player])
            self.selectable_tiles.remove(self.selected_tile)
            terrain.tile = self.selected_tile
            self.players[self.active_player].placed_tiles.append(self.selected_tile)
            self.selected_tile = None
            self.update_terrain_and_neighbors(terrain)
            self.update_scores(terrain)
            self.draw_new_tile()
            self.next_player()

    def select_tile(self, tile, notify_server = True):
        '''
        called by touch handler for local player, or by AI or network
        player to select a tile
        '''
        if self.selected_tile is not None and self.selected_tile != tile:
            self.selected_tile.selected = False
            self.selected_tile = None
        if not self.game_over and self.selected_tile is None and tile in self.selectable_tiles:
            tile_num = self.selectable_tiles.index(tile)
            tile.selected = True
            self.selected_tile = tile
        return False


    def on_touch_down_terrain(self, terrain, touch):
        if self.game_over:
            return True
        if self.selected_tile is None:
            return True
        if self.selected_tile.score_terrain[terrain.code] is None:
            return True
        player = self.players[self.active_player]
        if not player.local_control:
            return True
        if len(player.placed_tiles)>0:
            has_neighbor = False
            for t in self.neighbor_iter(terrain.hex_pos):
                if t.tile in player.placed_tiles:
                    has_neighbor = True
                    break
            if not has_neighbor:
                return True
        return self.place_tile(terrain)

    def on_touch_down_tile(self, tile, touch):
        if self.game_over:
            return True
        if tile.hex_pos != [-1, -1]:
            return True
        p = self.players[self.active_player]
        if not p.local_control:
            return True
        else:
            self.w_state_label.text = 'Place tile'
            self.w_state_label.color = color_average(white, p.color)
        return self.select_tile(tile)

class ScoreBoard(BoxLayout):
    def __init__(self):
        super(ScoreBoard, self).__init__(orientation = 'horizontal')
    def update_size(self, board_size):
        self.spacing = 0.01*board_size[0]

class PlayerScore(FloatLayout):
    ident = StringProperty()
    color = ListProperty()
    score = NumericProperty()
    active_turn = BooleanProperty(False)
    def __init__(self, identity, color):
        super(PlayerScore, self).__init__()
        self.ident = identity
        self.color = color

class Player(object):
    def __init__(self, name, color, board):
        self.local_control = True
        self.name = name
        self.color = color
        self.board = board
        self.placed_tiles = []
        self.score_marker = PlayerScore(identity = self.name[0:2], color = color)
        self.board.scoreboard.add_widget(self.score_marker)

    def delete(self):
        self.reset()
        self.board.scoreboard.remove_widget(self.score_marker)
        for pt in self.placed_tiles:
            self.board.remove_widget(pt)
        self.placed_tiles = []

    def reset(self):
        self.score_marker.active_turn = False
        self.score_marker.score = 0
        for pt in self.placed_tiles:
            self.board.remove_widget(pt)
        self.placed_tiles = []

    def start_turn(self):
        self.score_marker.active_turn = True

    def end_turn(self):
        self.score_marker.active_turn = False

    def board_resize(self, pos, board_size, hex_side):
        for pt in self.placed_tiles:
            pt.size = [hex_side*2, hex_side*2]
            pt.center = self.board.pixel_pos(pt.hex_pos)

class AIPlayer(Player):
    def __init__(self, name, color, board, tiles_count = None):
        super(AIPlayer, self).__init__(name, color, board, tiles_count)
        self.local_control = False

    def score_add_tile(self, value, hex_pos):
        placed = len([t for t in self.board.neighbor_iter(hex_pos) if t.tile is not None])
        score = value - placed
        if score == 0:
            score = 2
        elif score > 0 and placed > 0:
            score = 1
        elif score < 0:
            score = -1
        else:
            score = 0
        return score

    def score_remove_tile(self, value, hex_pos):
        placed = len([t for t in self.board.neighbor_iter(hex_pos) if t.tile is not None])
        score = value - placed
        if score == 0:
            score = -2
        elif score == 1:
            score = 2
        elif score > 1 and placed > 0:
            score = -1
        elif score < 0:
            score = 1
        else:
            score = 0
        return score

    def score_remove_neighbor(self, value, hex_pos):
        placed = len([t for t in self.board.neighbor_iter(hex_pos) if t.tile is not None])
        score = value - placed
        if score == -1: #remove to lock tile is good
            score = 2
        elif score == 0: #removing from a locked tile is bad
            score = -2
        elif score < -1 and placed > 0: #removing a tile that already has neigbors is good
            score = 1
        elif score > 0: #adding a tile that already has too many neighbors is bad
            score = -1
        else:
            score = 0
        return score

    def score_add_neighbor(self, value, hex_pos):
        placed = len([t for t in self.board.neighbor_iter(hex_pos) if t.tile is not None])
        score = value - placed
        if score == 0: #adding to a locked tile is bad
            score = -2
        elif score == 1: #adding to lock a tile is good
            score = 2
        elif score > 1 and placed > 0: #adding a tile that already has neigbors is good
            score = 1
        elif score < 0: #adding a tile that already has too many neighbors is bad
            score = -1
        else:
            score = 0
        return score

    def start_turn(self):
        super(AIPlayer, self).start_turn()
        Clock.schedule_once(self.select_turn, 0.7)

    def select_turn(self, *args):
        tile = self.evaluate_tile_select()
        self.board.select_tile(tile)
        Clock.schedule_once(self.place_turn, 0.7)

    def place_turn(self, *args):
        terrain = self.evaluate_tile_place()
        self.board.place_tile(terrain)

    def evaluate_tile_select(self):
        select_scores = []
        for x,d in zip(range(self.tiles_count), self.tiles):
            if d.hex_pos != [-1, -1]:
                score = self.score_remove_tile(d.value, d.hex_pos) ##TODO: incentive to do this is not strong while score is low
                if score>0:
                    score=0
                self.board.neighbor_iter(d.hex_pos)
                for t in self.board.neighbor_iter(d.hex_pos):
                    if t.tile is not None:
                        if t.tile.player == self:
                            score += self.score_remove_neighbor(t.tile.value, t.tile.hex_pos) ##TODO: only give weight to players with scores above, say, 4
                        else:
                            if t.tile.player.score_marker.score > 3:
                                score -= self.score_remove_neighbor(t.tile.value, t.tile.hex_pos)
            else: #prefer to select tiles from the stack if opponents scores are low enough
                if max([p.score_marker.score for p in self.board.players])>4:
                    score = 0
                else:
                    score = 2
            select_scores.append(score)
        max_score = max(select_scores)
        candidates = [self.tiles[x] for x in range(self.tiles_count) if select_scores[x] == max_score]
        return random.choice(candidates)

    def evaluate_tile_place(self):
        #TODO: if this takes time, chunk it up and call repeatedly using a timer
        value = self.board.selected_tile.value
        max_score = -1000
        candidates = []
        for hp in self.board.terrain:
            t = self.board.terrain[hp]
            if t.tile is None:
                score = self.score_add_tile(value, hp)
                n = list(self.board.neighbor_iter(hp))
                if value > len(n) and score > 0:
                    score -= 2
                for t1 in n:
                    if t1.tile is not None:
                        if t1.tile.player == self:
                            score += self.score_add_neighbor(t1.tile.value, t1.tile.hex_pos)
                        else:
                            score -= self.score_add_neighbor(t1.tile.value, t1.tile.hex_pos)
                if score == max_score:
                    candidates.append(t)
                elif score > max_score:
                    candidates = [t]
                    max_score = score
        return random.choice(candidates)


class NetworkPlayer(Player):
    def __init__(self, name, color, board, tiles_count = None):
        super(NetworkPlayer, self).__init__(name, color, board, tiles_count)
        self.local_control = False
        self.queue = None

    def start_turn(self):
        super(NetworkPlayer, self).start_turn()


class GameScreen(BoxLayout):
    def __init__(self):
        super(GameScreen, self).__init__()
        self.board = Board()
        self.add_widget(self.board)

class PlayerSpec:
    def __init__(self, name, color, type):
        self.name = name
        self.color = color
        self.type = type

color_lookup = {
    0: [0.6, 0, 0, 1],
    1: [0, 0.6, 0, 1],
    2: [0, 0, 0.6, 1],
    3: [0.5, 0, 0.5, 1],
    4: [0.5, 0.5, 0, 1],
    }

class LevelHex(FloatLayout):
    source_id = StringProperty('tiles/terrain_plain.png')
    level_id = StringProperty('1')

    def __init__(self, level_id, source_id = None):
        super(LevelHex, self).__init__()
        self.lid = level_id
        self.level_id = str(level_id)
        self.size_hint = [None, None]
        if source_id is not None:
            self.source_id = source_id

    def on_touch_up(self, touch):
        if (touch.pos[0] - self.center_x)**2 + (touch.pos[1] - self.center_y)**2 < (self.size[0]/2)**2:
            self.parent.on_touch_up_level(self, touch)


class LevelPicker(FloatLayout):
    def __init__(self, game_menu):
        super(LevelPicker, self).__init__()
        self.levels = dict([(l.id,l) for l in levels.Level.__subclasses__()])
        self.game_menu = game_menu
        for i in sorted(self.levels):
            self.add_widget(LevelHex(i))
        self.bind(size=self.on_size)

    def on_size(self, *args):
        W = self.size[0]
        H = self.size[1]
        N = len(self.children)
        if W==0 or W is None or N == 0:
            return
        x = math.ceil((1.0*N*W/H)**0.5)
        y = math.ceil(1.0*x/N)
        i = 0
        for w in reversed(self.children):
            w.size = [W*0.1, H*0.1]
            w.center = [(i+1)*3*w.size[0],self.size[1]/2]
            i += 1

    def on_touch_up_level(self, terrain, touch):
        self.game_menu.start_sp_game(self.levels[terrain.lid])


class GameMenu(ScreenManager):
    player_count = NumericProperty()
    players = ListProperty()
    w_game = ObjectProperty()

    def __init__(self):
        super(GameMenu, self).__init__()

    def restart_game(self):
        board = self.w_game.children[0]
        board.setup_game(self.player_spec)
        board.start_game()
        self.current = 'game'

    def start_game(self, *args):
        ps = PlayerSpec('Player '+str(1), color_lookup[0], 0)
        self.player_spec = [ps]
        board = self.w_game.children[0]
        board.setup_game(self.player_spec)
        board.start_game()
        self.current = 'game'

    def start_sp_game(self, level):
        board = self.w_game.children[0]
        self.player_spec = [PlayerSpec('Player '+str(1), purple, 0)]
        board.setup_game(self.player_spec, level)
        board.start_game()
        self.current = 'game'

class GameApp(App):
    def build(self):
        self.gm = GameMenu()
        self.gm.w_game.add_widget(Board())
        self.gm.w_singleplayer.add_widget(LevelPicker(self.gm))
        Window.bind(on_keyboard = self.on_keyboard)
        return self.gm

    def on_keyboard(self, window, key, scancode=None, codepoint=None, modifier=None):
        '''
        used to manage the effect of the escape key
        '''
        if key == 27:
            if self.gm.current == 'main':
                return False
            elif self.gm.current == 'host_game':
                self.gm.current = 'main'
            elif self.gm.current == 'host_wait':
                self.gm.current = 'main'
            elif self.gm.current == 'join_game':
                self.gm.current = 'main'
            elif self.gm.current == 'game':
                self.gm.current = 'pause'
            elif self.gm.current == 'pause':
                self.gm.current = 'game'
            return True
        return False

    def on_pause(self):
        '''
        trap on_pause to keep the app alive on android
        '''
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        pass

if __name__ == '__main__':
    Builder.load_file('pk.kv')
    gameapp = GameApp()
    gameapp.run()
