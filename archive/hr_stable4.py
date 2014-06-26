#!/usr/bin/python
"""
    copyright 2008  - Johannes 'josch' Schauer <j.schauer@email.de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import pyglet
import random
import itertools
import sys

if sys.version_info[:2] >= (2,6):
    import json
else:
    try:
        import simplejson as json
    except ImportError:
        import demjson as json
        json.loads = json.decode

IF_BOTTOM = 48
IF_RIGHT = 200
IF_TOP = IF_LEFT = 8

class Animation(object):
    def __init__(self, frames):
        self.frames = frames
        self.animation = 0
    
    def get_current_frame(self):
        return self.frames[self.animation]
    
    def get_next_frame(self):
        self.animation = (self.animation+1)%len(self.frames)
        return self.frames[self.animation]

class WaterTile(Animation):
    def __init__(self, tiles):
        super(WaterTile, self).__init__(tiles)
        self.tiles = tiles
    
    def get_tex_coords(self):
        return self.get_current_frame().tex_coords
    
    def get_next_tex_coords(self):
        return self.get_next_frame().tex_coords

class Tile(object):
    def __init__(self, tile):
        self.tile = tile
    
    def get_tex_coords(self):
        return self.tile.tex_coords
        
    def get_next_tex_coords(self):
        return self.tile.tex_coords

class MapSet(object):
    def __init__(self, loaded_map):
        self.width = len(loaded_map[0])
        self.height = len(loaded_map)
        
        atlas = pyglet.image.atlas.TextureAtlas(width=2048, height=2048)
        self.group = pyglet.graphics.TextureGroup(atlas.texture)
        self.grass_tiles = [atlas.add(pyglet.image.load('data/tiles/grass/%d.png'%i)) for i in xrange(79)]
        self.snow_tiles = [atlas.add(pyglet.image.load('data/tiles/snow/%d.png'%i)) for i in xrange(79)]
        self.lava_tiles = [atlas.add(pyglet.image.load('data/tiles/lava/%d.png'%i)) for i in xrange(79)]
        self.swamp_tiles = [atlas.add(pyglet.image.load('data/tiles/swamp/%d.png'%i)) for i in xrange(79)]
        self.rough_tiles = [atlas.add(pyglet.image.load('data/tiles/rough/%d.png'%i)) for i in xrange(79)]
        self.dirt_tiles = [atlas.add(pyglet.image.load('data/tiles/dirt/%d.png'%i)) for i in xrange(46)]
        self.rock_tiles = [atlas.add(pyglet.image.load('data/tiles/rock/%d.png'%i)) for i in xrange(48)]
        self.sand_tiles = [atlas.add(pyglet.image.load('data/tiles/sand/%d.png'%i)) for i in xrange(24)]
        self.water_tiles = [[atlas.add(pyglet.image.load('data/tiles/water/%d watrtl%02d.pcx/%d.png'%(j,j+1,i))) for i in xrange(12)] for j in xrange(33)]
        self.edge_tiles = [atlas.add(pyglet.image.load('data/tiles/edge/%d EDG%d.PCX'%(i, i+1))) for i in xrange(36)]
        
        self.tiles = [[Tile(self.grass_tiles[0]) for i in xrange(self.width)] for j in xrange(self.height)]
        for y, line in enumerate(loaded_map):
            for x, tile in enumerate(line):
                if tile[0] == -1: #edge
                    self.tiles[y][x] = Tile(self.edge_tiles[tile[1]])
                elif tile[0] == 0: #dirt
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[y][x] = Tile(self.dirt_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y))
                    else:
                        self.tiles[y][x] = Tile(self.dirt_tiles[tile[1]])
                elif tile[0] == 1: #sand
                    self.tiles[y][x] = Tile(self.sand_tiles[tile[1]])
                elif tile[0] == 2: #grass
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[y][x] = Tile(self.grass_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y))
                    else:
                        self.tiles[y][x] = Tile(self.grass_tiles[tile[1]])
                elif tile[0] == 3: #snow
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[y][x] = Tile(self.snow_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y))
                    else:
                        self.tiles[y][x] = Tile(self.snow_tiles[tile[1]])
                elif tile[0] == 4: #swamp
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[y][x] = Tile(self.swamp_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y))
                    else:
                        self.tiles[y][x] = Tile(self.swamp_tiles[tile[1]])
                elif tile[0] == 5: #rough
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[y][x] = Tile(self.rough_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y))
                    else:
                        self.tiles[y][x] = Tile(self.rough_tiles[tile[1]])
                elif tile[0] == 7: #lava
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[y][x] = Tile(self.lava_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y))
                    else:
                        self.tiles[y][x] = Tile(self.lava_tiles[tile[1]])
                elif tile[0] == 8: #water
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        tiles = []
                        for tile in self.water_tiles[tile[1]]:
                            tiles.append(tile.get_transform(flip_x=flip_x, flip_y=flip_y))
                        self.tiles[y][x] = WaterTile(tiles)
                    else:
                        self.tiles[y][x] = WaterTile(self.water_tiles[tile[1]])
                elif tile[0] == 9: #rock
                    self.tiles[y][x] = Tile(self.rock_tiles[tile[1]])
                else:
                    print tile[0]
                    self.tiles[y][x] = GrassTile(self.grass_tiles[0])
    
    def get_tile(self, x, y):
        assert x >= 0 and y >= 0
        return self.tiles[y][x]

class MapView(object):
    def __init__(self, mapset, window):
        self.window = window
        self.mapset = mapset
        
        self._init_view()
        
        pyglet.clock.schedule_interval(self.animate_water, 1/6.0)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
    
    def _init_view(self):
        self.tile_size = 32
        #step one tile
        self.steps = self.tile_size
        
        self.viewport_x = self.window.width-IF_RIGHT-IF_LEFT
        self.viewport_y = self.window.height-IF_BOTTOM-IF_TOP
        
        #drawn tiles
        self.tiles_x = min((self.viewport_x//self.tile_size)+2, self.mapset.width)
        self.tiles_y = min((self.viewport_y//self.tile_size)+2, self.mapset.height)

        self.center_x = False
        if self.mapset.width*self.tile_size < self.viewport_x:
            self.center_x = True
            self.global_x = (self.mapset.width*self.tile_size)//2-(self.viewport_x//2)
        self.center_y = False
        if self.mapset.height*self.tile_size < self.viewport_y:
            self.center_y = True
            self.global_y = (self.mapset.height*self.tile_size)//2-(self.viewport_y//2)
        
        #undrawn map size
        self.undrawn_x = self.tile_size*(self.mapset.width-self.tiles_x)
        self.undrawn_y = self.tile_size*(self.mapset.height-self.tiles_y)
        #size of full undrawn steps
        self.undrawn_steps_x = self.steps*(self.undrawn_x//self.steps)
        self.undrawn_steps_y = self.steps*(self.undrawn_y//self.steps)
        
        self.vertex_list = [[] for i in xrange(self.tiles_y)]
        self.batch = pyglet.graphics.Batch()
        
        self.view_x = 0
        self.view_y = 0
        self.global_x = (self.mapset.width*self.tile_size)//2-(self.viewport_x//2)
        self.global_y = (self.mapset.height*self.tile_size)//2-(self.viewport_y//2)
        self.dx = 0
        self.dy = 0
        
        #here we translate the global map position so we can draw with it
        trans_global_x = self.steps-self.global_x
        trans_global_y = self.steps-self.global_y
        
        if trans_global_x < -self.undrawn_steps_x:
            mod_x = trans_global_x+self.undrawn_x
        elif trans_global_x < self.steps:
            mod_x = trans_global_x%self.steps
        else:
            mod_x = trans_global_x
        
        if trans_global_y < -self.undrawn_steps_y:
            mod_y = trans_global_y+self.undrawn_y
        elif trans_global_y < self.steps:
            mod_y = trans_global_y%self.steps
        else:
            mod_y = trans_global_y
        
        self.div_x = (trans_global_x-mod_x)//self.tile_size
        self.div_y = (trans_global_y-mod_y)//self.tile_size+self.mapset.height-1
        
        vertices = []
        tex_coords = []
        count = 0
        
        for y in xrange(self.tiles_y):
            y1 = y*32+IF_BOTTOM
            y2 = y1+32
            for x in xrange(self.tiles_x):
                x1 = x*32+IF_LEFT
                x2 = x1+32
                tile = self.mapset.get_tile(x-self.div_x, self.div_y-y)
                self.vertex_list[y].append(self.batch.add(4, pyglet.gl.GL_QUADS, self.mapset.group,
                                    ('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
                                    ('t3f', tile.get_tex_coords()),
                                    ('c4B', (255,255,255,255)*4)))
        self.view_x = mod_x-self.steps
        self.view_y = mod_y-self.steps
    
    def on_draw(self):
        pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT)
        pyglet.gl.glPushMatrix()
        pyglet.gl.glTranslatef(self.view_x, self.view_y, 0)
        pyglet.gl.glScalef(self.tile_size/32.0, self.tile_size/32.0, 0.0)
        self.batch.draw()
        pyglet.gl.glPopMatrix()
        pyglet.gl.glLoadIdentity()
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glColor4f(1, 0, 1, 1)
        pyglet.gl.glRectf(0, 0, self.window.width, IF_BOTTOM)
        pyglet.gl.glRectf(self.window.width-IF_RIGHT, 0, self.window.width, self.window.height)
        pyglet.gl.glRectf(0, self.window.height-IF_TOP, self.window.width, self.window.height)
        pyglet.gl.glRectf(0, 0, IF_LEFT, self.window.height)
    
    def _move(self, dx, dy):
        retex = False
        
        #here we translate the global map position so we can draw with it
        trans_global_x = self.steps-self.global_x
        trans_global_y = self.steps-self.global_y
        
        new_global_x = trans_global_x+dx
        new_global_y = trans_global_y+dy
        
        if self.global_x-dx < 0:
            new_global_x = self.steps
        if self.global_y-dy < 0:
            new_global_y = self.steps
        if dx-self.global_x < -self.tile_size*self.mapset.width+self.viewport_x:
            new_global_x = -self.tile_size*self.mapset.width+self.viewport_x+self.steps
        if dy-self.global_y < -self.tile_size*self.mapset.height+self.viewport_y:
            new_global_y = -self.tile_size*self.mapset.height+self.viewport_y+self.steps
        
        if new_global_x < -self.undrawn_steps_x:
            mod_x = new_global_x+self.undrawn_x
            if trans_global_x >= -self.undrawn_steps_x:
                retex = True
        elif new_global_x < self.steps:
            div_x, mod_x = divmod(new_global_x, self.steps)
            retex = div_x != trans_global_x//self.steps or retex
        else:
            mod_x = new_global_x
        
        if new_global_y < -self.undrawn_steps_y:
            mod_y = new_global_y+self.undrawn_y
            if trans_global_y >= -self.undrawn_steps_y:
                retex = True
        elif new_global_y < self.steps:
            div_y, mod_y = divmod(new_global_y, self.steps)
            retex = div_y != trans_global_y//self.steps or retex
        else:
            mod_y = new_global_y
        
        if retex:
            self.div_x = (new_global_x-mod_x)//self.tile_size
            self.div_y = (new_global_y-mod_y)//self.tile_size+self.mapset.height-1
            for y in xrange(self.tiles_y):
                for x in xrange(self.tiles_x):
                    tile = self.mapset.get_tile(x-self.div_x, self.div_y-y)
                    self.vertex_list[y][x].tex_coords = tile.get_tex_coords()
        
        if not self.center_x:
            self.view_x = mod_x-self.steps
            self.global_x = self.steps-new_global_x
        if not self.center_y:
            self.view_y = mod_y-self.steps
            self.global_y = self.steps-new_global_y
    
    def update(self, dt):
        try:
            if self.window.keys[pyglet.window.key.LCTRL] and \
               any([self.window.keys[pyglet.window.key.UP],
                    self.window.keys[pyglet.window.key.DOWN],
                    self.window.keys[pyglet.window.key.LEFT],
                    self.window.keys[pyglet.window.key.RIGHT]]):
                
                if self.window.keys[pyglet.window.key.LEFT]:
                    x = 1
                elif self.window.keys[pyglet.window.key.RIGHT]:
                    x = -1
                else:
                    x = 0
                
                if self.window.keys[pyglet.window.key.UP]:
                    y = -1
                elif self.window.keys[pyglet.window.key.DOWN]:
                    y = 1
                else:
                    y = 0
                self.dx += x*8
                self.dy += y*8
        except KeyError:
            pass
        if self.dx or self.dy:
            self._move(self.dx, self.dy)
            self.dx = 0
            self.dy = 0
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.dx += dx
        self.dy += dy
        return pyglet.event.EVENT_HANDLED
    
    def on_resize(self, width, height):
        self._init_view()
    
    def animate_water(self, dt):
        for y in xrange(self.tiles_y):
            for x in xrange(self.tiles_x):
                tile = self.mapset.get_tile(x-self.div_x, self.div_y-y)
                if isinstance(tile, WaterTile):
                    self.vertex_list[y][x].tex_coords = tile.get_next_tex_coords()

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(800, 600, resizable=True, vsync=False )
        img = pyglet.resource.image("data/cursors/default.png")
        self.set_mouse_cursor(pyglet.window.ImageMouseCursor(img, 0, 40))
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.fps = pyglet.clock.ClockDisplay()
    
    def on_draw(self):
        self.fps.draw()
    
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.F11:
            self.set_fullscreen(fullscreen=not self.fullscreen)
    
    def empty(self, dt):
        pass

def main():
    pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    window = Window()
    
    h3m = json.loads(open("test.h3m").read())
    loaded_map = h3m["upper_terrain"]
    
    edge_map = [[] for i in xrange(len(loaded_map)+16)]
    for num in xrange(len(edge_map)):
        if num < 7 or num > len(edge_map)-8:
            line = []
            line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(len(loaded_map[0])+18)])
        elif num == 7:
            line = []
            line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            line.append([-1, 16, 0, 0, 0, 0, 0])
            line.extend([[-1, 20+i%4, 0, 0, 0, 0, 0] for i in xrange(len(loaded_map[0]))])
            line.append([-1, 17, 0, 0, 0, 0, 0])
            line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
        elif num == len(edge_map)-8:
            line = []
            line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            line.append([-1, 19, 0, 0, 0, 0, 0])
            line.extend([[-1, 28+i%4, 0, 0, 0, 0, 0] for i in xrange(len(loaded_map[0]))])
            line.append([-1, 18, 0, 0, 0, 0, 0])
            line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
        else:
            line = []
            line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            line.append([-1, 32+num%4, 0, 0, 0, 0, 0])
            line.extend(loaded_map[num-8])
            line.append([-1, 24+num%4, 0, 0, 0, 0, 0])
            line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
        edge_map[num] = line
    mapset = MapSet(edge_map)
    
    mapview = MapView(mapset, window)
    window.push_handlers(mapview)
    pyglet.clock.schedule(window.empty)
    pyglet.app.run()

if __name__ == '__main__':
    main()
