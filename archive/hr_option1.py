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
    def __init__(self, tiles, group):
        super(WaterTile, self).__init__(tiles)
        self.tiles = tiles
        self.group = group
    
    def get_group(self):
        return self.group
    
    def get_tex_coords(self):
        return self.get_current_frame().tex_coords
    
    def get_next_tex_coords(self):
        return self.get_next_frame().tex_coords

class GrassTile(object):
    def __init__(self, tile, group):
        self.tile = tile
        self.group = group
    
    def get_group(self):
        return self.group
        
    def get_tex_coords(self):
        return self.tile.tex_coords

class MapSet(object):
    def __init__(self, loaded_map):
        self.width = len(loaded_map[0])
        self.height = len(loaded_map)
        
        self.water_tiles = self._load_water_tiles()
        self.grass_tiles = self._load_grass_tiles()
        
        self.tiles = [[None for i in xrange(self.width)] for j in xrange(self.height)]
        for y, line in enumerate(loaded_map):
            for x, tile in enumerate(line):
                if tile[0] == 2: #grass
                    self.tiles[y][x] = GrassTile(self.grass_tiles[tile[1]], self.grass_group)
                elif tile[0] == 8: #water
                    self.tiles[y][x] = WaterTile(self.water_tiles[tile[1]], self.water_group)
    
    def _load_grass_tiles(self):
        atlas = pyglet.image.atlas.TextureAtlas()
        self.grass_texture = atlas.texture
        self.grass_group = pyglet.graphics.TextureGroup(atlas.texture)
        return [atlas.add(pyglet.image.load('data/tiles/grass/0.png'))]
    
    def _load_water_tiles(self):
        atlas = pyglet.image.atlas.TextureAtlas(width=384, height=416)
        self.water_texture = atlas.texture
        self.water_group = pyglet.graphics.TextureGroup(atlas.texture)
        return [[atlas.add(pyglet.image.load('data/tiles/water/%d watrtl%d.pcx/%d.png'%(j,j+1,i))) for i in xrange(12)] for j in xrange(20, 32)]
    
    def get_tile(self, x, y):
        assert x >= 0 and y >= 0
        return self.tiles[y][x]

class MapView(object):
    def __init__(self, mapset, window):
        self.window = window
        self.mapset = mapset
        
        self.batch = pyglet.graphics.Batch()
        
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = 0
        
        self.vertex_lists = {}
        
        self._init_view()
        
        pyglet.clock.schedule_interval(self.animate_water, 1/6.0)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
    
    def _init_view(self):
        for vlist in self.vertex_lists.values():
            vlist.delete()
        self.vertex_lists = {}
        coords = {}
        textures = {}
        
        div_y, mod_y = divmod(self.y, 32)
        div_x, mod_x = divmod(self.x, 32)
        for y in xrange((self.window.height-48)//32):
            y1 = mod_y+y*32+48
            y2 = y1+32
            for x in xrange((self.window.width-192)//32):
                x1 = mod_x+x*32
                x2 = x1+32
                tile = self.mapset.get_tile(x-div_x, y-div_y)
                group = tile.get_group()
                if group not in coords.keys():
                    coords[group] = []
                    textures[group] = []
                
                coords[group].extend([x1, y1, x2, y1, x2, y2, x1, y2])
                textures[group].extend(tile.get_tex_coords())
        
        for group in coords.keys():
            self.vertex_lists[group] = self.batch.add((len(coords[group])//8)*4, pyglet.gl.GL_QUADS, group,
                                            ('v2i', coords[group]),
                                            ('t3f', textures[group]),
                                            ('c4B', (255,255,255,255) * (len(coords[group])//8)*4))
    
    def on_draw(self):
        pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT | pyglet.gl.GL_DEPTH_BUFFER_BIT)
        self.batch.draw()
    
    def _move(self, dx, dy):
        div_y, mod_y = divmod(self.y+dy, 32)
        div_x, mod_x = divmod(self.x+dx, 32)
        
        if div_x != self.x//32 or div_y != self.y//32:
            update_texture = True
        else:   
            update_texture = False
        
        self.x += dx
        self.y += dy
        if update_texture:
            self._init_view()
        else:
            coords = {}
            
            for y in xrange((self.window.height-48)//32):
                y1 = mod_y+y*32+48
                y2 = y1+32
                for x in xrange((self.window.width-192)//32):
                    x1 = mod_x+x*32
                    x2 = x1+32
                    
                    tile = self.mapset.get_tile(x-div_x, y-div_y)
                    group = tile.get_group()
                    if group not in coords.keys():
                        coords[group] = []
                    coords[group].extend([x1, y1, x2, y1, x2, y2, x1, y2])
            for group in coords.keys():
                self.vertex_lists[group].vertices = coords[group]
    
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
        water_texture = []
        for y in xrange((self.window.height-48)//32):
            for x in xrange((self.window.width-192)//32):
                tile = self.mapset.get_tile(x-self.x//32, y-self.y//32)
                if tile.get_group() is self.mapset.water_group:
                    water_texture.extend(tile.get_next_tex_coords())
        self.vertex_lists[self.mapset.water_group].tex_coords = water_texture

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
    
    loaded_map = [[[8,random.randint(0,11)] for x in xrange(128)] for y in xrange(128)]
    loaded_map[10][10] = [2, 0]
    loaded_map[0] = [[2,0] for y in xrange(128)]
    for x in xrange(128):
        loaded_map[x][32] = [2,0]
    mapset = MapSet(loaded_map)
    
    mapview = MapView(mapset, window)
    window.push_handlers(mapview)
    pyglet.clock.schedule(window.empty)
    pyglet.app.run()

if __name__ == '__main__':
    main()
