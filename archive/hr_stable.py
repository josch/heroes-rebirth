#!/usr/bin/python

import pyglet
import random

class Map(object):
    def __init__(self, window):
        self.window = window
    
        #generate map
        self.water_map = [[random.randint(0,11) for x in xrange(128)] for y in xrange(128)]
        
        self.batch = pyglet.graphics.Batch()
        
        self.animate = 0
        
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = 0
        
        self.vertex_lists = [[] for x in xrange((self.window.height-48)//32)]
        
        self._load_resources()
        self._init_map()
        
        pyglet.clock.schedule_interval(self.animate_water, 1/6.0)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
        
    def _load_resources(self):
        atlas = pyglet.image.atlas.TextureAtlas(width=384, height=416)
        self.tiles = [[atlas.add(pyglet.image.load('data/tiles/water/%d watrtl%d.pcx/%d.png'%(j,j+1,i))) for i in xrange(12)] for j in xrange(20, 32)]
        self.water_texture = atlas.texture
    
    def _init_map(self):
        try:
            for row in self.vertex_lists:
                for vlist in row:
                    vlist.delete()
        except:
            raise
        self.vertex_lists = [[] for x in xrange((self.window.height-48)//32)]
        group = pyglet.graphics.TextureGroup(self.water_texture)
        for y in xrange((self.window.height-48)//32):
            y1 = y*32+48
            y2 = y1+32
            for x in xrange((self.window.width-192)//32):
                x1 = x*32
                x2 = x1+32
                tile = self.tiles[self.water_map[y][x]][self.animate]
                self.vertex_lists[y].append(self.batch.add(4, pyglet.gl.GL_QUADS, group,
                                            ('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
                                            ('t3f', tile.tex_coords),
                                            ('c4B', (255,255,255,255) * 4)))
    
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
        
        for y in xrange((self.window.height-48)//32):
            y1 = mod_y+y*32+48
            y2 = y1+32
            for x in xrange((self.window.width-192)//32):
                x1 = mod_x+x*32
                x2 = x1+32
                self.vertex_lists[y][x].vertices = [x1, y1, x2, y1, x2, y2, x1, y2]
                
                if update_texture:
                    tile = self.tiles[self.water_map[y-div_y][x-div_x]][self.animate]
                    self.vertex_lists[y][x].tex_coords=tile.tex_coords
    
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
        self._init_map()
    
    def animate_water(self, dt):
        for y in xrange((self.window.height-48)//32):
            for x in xrange((self.window.width-192)//32):
                tile = self.tiles[self.water_map[y-self.y//32][x-self.x//32]][self.animate]
                self.vertex_lists[y][x].tex_coords=tile.tex_coords
        self.animate = (self.animate+1)%12

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(800, 600, resizable=True, vsync=False )
        img = pyglet.resource.image("data/cursors/default.png")
        self.set_mouse_cursor(pyglet.window.ImageMouseCursor(img, 4, 28))
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.fps = pyglet.clock.ClockDisplay()
    
    def on_draw(self):
        self.fps.draw()
    
    def empty(self, dt):
        pass

def main():
    pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    window = Window()
    map = Map(window)
    window.push_handlers(map)
    pyglet.clock.schedule(window.empty)
    pyglet.app.run()

if __name__ == '__main__':
    main()
