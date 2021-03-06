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

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import demjson as json
        json.loads = json.decode
        json.dumps = json.encode

IF_BOTTOM = 48
IF_RIGHT = 200
IF_TOP = IF_LEFT = 8

class OrderedTextureGroup(pyglet.graphics.Group):
    def __init__(self, order, texture, parent=None):
        super(OrderedTextureGroup, self).__init__(parent)
        self.texture = texture
        self.order = order

    def set_state(self):
        pyglet.gl.glEnable(self.texture.target)
        pyglet.gl.glBindTexture(self.texture.target, self.texture.id)

    def unset_state(self):
        pyglet.gl.glDisable(self.texture.target)

    def __hash__(self):
        return hash((self.order, self.texture.target, self.texture.id, self.parent))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
            self.order == other.order and
            self.texture.target == other.texture.target and
            self.texture.id == other.texture.id and
            self.parent == self.parent)

    def __repr__(self):
        return '%s(id=%d)' % (self.__class__.__name__, self.order, self.texture.id)
        
    def __cmp__(self, other):
        if isinstance(other, OrderedTextureGroup):
            return cmp(self.order, other.order)
        return -1

class Animation(object):
    def __init__(self, frames):
        self.__frames = frames
        self.__animation = 0
    
    def get_tex_coords(self):
        return self.__frames[self.__animation].tex_coords
    
    tex_coords = property(get_tex_coords)
    
    def get_next_tex_coords(self):
        self.__animation = (self.__animation+1)%len(self.__frames)
        return self.__frames[self.__animation].tex_coords
        
    next_tex_coords = property(get_next_tex_coords)

class MapSet(object):
    def __init__(self, loaded_map, objects, tunedobj):
        self.width = len(loaded_map[0])
        self.height = len(loaded_map)
        
        #print len(pyglet.resource._default_loader._index)
        
        atlas = pyglet.image.atlas.TextureAtlas(width=1024, height=1024)
        atlas2 = pyglet.image.atlas.TextureAtlas(width=2048, height=2048)
        self.texture_group = pyglet.graphics.TextureGroup(atlas.texture)
        self.group = pyglet.graphics.OrderedGroup(0, self.texture_group)
        self.texture_group2 = pyglet.graphics.TextureGroup(atlas2.texture)
        self.group_obj = pyglet.graphics.OrderedGroup(1, self.texture_group2)
        self.grass_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/grastl.def/%d.png'%i))) for i in xrange(79)]
        self.snow_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/snowtl.def/%d.png'%i))) for i in xrange(79)]
        self.lava_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/lavatl.def/%d.png'%i))) for i in xrange(79)]
        self.swamp_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/swmptl.def/%d.png'%i))) for i in xrange(79)]
        self.rough_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/rougtl.def/%d.png'%i))) for i in xrange(79)]
        self.dirt_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/dirttl.def/%d.png'%i))) for i in xrange(46)]
        self.rock_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/rocktl.def/%d.png'%i))) for i in xrange(48)]
        self.sand_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/sandtl.def/%d.png'%i))) for i in xrange(24)]
        self.water_tiles = [[atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/watrtl.def/%d/%d.png'%(j,i)))) for i in xrange(12)] for j in xrange(33)]
        self.edge_tiles = [atlas.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/edg.def/%d.png'%i))) for i in xrange(36)]
        self.tiles = {}
        for y, line in enumerate(loaded_map):
            for x, tile in enumerate(line):
                if tile[0] == -1: #edge
                    self.tiles[x,y] = Tile(self.edge_tiles[tile[1]])
                elif tile[0] == 0: #dirt
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[x,y] = self.dirt_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        self.tiles[x,y] = self.dirt_tiles[tile[1]]
                elif tile[0] == 1: #sand
                    self.tiles[x,y] = self.sand_tiles[tile[1]]
                elif tile[0] == 2: #grass
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[x,y] = self.grass_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        self.tiles[x,y] = self.grass_tiles[tile[1]]
                elif tile[0] == 3: #snow
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[x,y] = self.snow_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        self.tiles[x,y] = self.snow_tiles[tile[1]]
                elif tile[0] == 4: #swamp
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[x,y] = self.swamp_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        self.tiles[x,y] = self.swamp_tiles[tile[1]]
                elif tile[0] == 5: #rough
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[x,y] = self.rough_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        self.tiles[x,y] = self.rough_tiles[tile[1]]
                elif tile[0] == 7: #lava
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        self.tiles[x,y] = self.lava_tiles[tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        self.tiles[x,y] = self.lava_tiles[tile[1]]
                elif tile[0] == 8: #water
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        tiles = []
                        for tile in self.water_tiles[tile[1]]:
                            tiles.append(tile.get_transform(flip_x=flip_x, flip_y=flip_y))
                        self.tiles[x,y] = Animation(tiles)
                    else:
                        self.tiles[x,y] = Animation(self.water_tiles[tile[1]])
                elif tile[0] == 9: #rock
                    self.tiles[x,y] = self.rock_tiles[tile[1]]
                else:
                    raise NotImplementedError
        
        images = [(pyglet.image.load(None, file=pyglet.resource.file("data/map_objects/"+obj["filename"]+"/0.png")), i) for i,obj in enumerate(objects)]
        self.objects = [(atlas2.add(image[0]), image[1]) for image in sorted(images, key=lambda i:i[0].height, reverse=True)]
        self.objects = [i[0] for i in sorted(self.objects, key=lambda i:i[1])]
        
        self.tunedobj = {}
        for obj in [i for i in tunedobj if i["z"]==0]:
            if self.tunedobj.get((obj["x"], obj["y"]), None) is not None:
                self.tunedobj[obj["x"],obj["y"]].append(self.objects[obj["id"]])
            else:
                self.tunedobj[obj["x"],obj["y"]] = [self.objects[obj["id"]]]
        
        self.clrrvr = [atlas2.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/clrrvr.def/%d/0.png'%i))) for i in xrange(13)]
        
        for y, line in enumerate(loaded_map):
            for x, tile in enumerate(line):
                if tile[2] == 1: #clrrvr
                    flip_x = bool(tile[6] & 4)
                    flip_y = bool(tile[6] & 8)
                    if flip_x or flip_y:
                        c = self.clrrvr[tile[3]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        c = self.clrrvr[tile[3]]
                    if self.tunedobj.get((x, y), None) is not None:
                        self.tunedobj[x, y].append(c)
                    else:
                        self.tunedobj[x, y] = [c]
        
        
        self.dirtrd = [atlas2.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/dirtrd.def/%d.png'%i))) for i in xrange(17)]
        self.gravrd = [atlas2.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/gravrd.def/%d.png'%i))) for i in xrange(17)]
        self.cobbrd = [atlas2.add(pyglet.image.load(None, file=pyglet.resource.file('data/tiles/cobbrd.def/%d.png'%i))) for i in xrange(17)]

        for y, line in enumerate(loaded_map):
            for x, tile in enumerate(line):
                if tile[4] == 1: #dirtrd
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        c = self.dirtrd[tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        c = self.dirtrd[tile[5]]
                    if self.tunedobj.get((x, y), None) is not None:
                        self.tunedobj[x, y].append(c)
                    else:
                        self.tunedobj[x, y] = [c]
                elif tile[4] == 2: #gravrd
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        c = self.gravrd[tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        c = self.gravrd[tile[5]]
                    if self.tunedobj.get((x, y), None) is not None:
                        self.tunedobj[x, y].append(c)
                    else:
                        self.tunedobj[x, y] = [c]
                elif tile[4] == 3: #cobbrd
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        c = self.cobbrd[tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                    else:
                        c = self.cobbrd[tile[5]]
                    if self.tunedobj.get((x, y), None) is not None:
                        self.tunedobj[x, y].append(c)
                    else:
                        self.tunedobj[x, y] = [c]
        
class MapView(object):
    def __init__(self, mapset, window):
        self.window = window
        self.mapset = mapset
        
        self._first_time_init()
        self._init_view()
        
        #mouse position
        self.label = pyglet.text.Label('',
                font_name="",
                font_size=36,
                bold=True,
                color=(128, 128, 128, 128),
                x=self.window.width-10, y=0,
                anchor_x='right', anchor_y='bottom')
        
        pyglet.clock.schedule_interval(self.animate_water, 1/6.0)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
    
    def _first_time_init(self):
        self.tile_size = 32
        self.viewport_x = self.window.width-IF_RIGHT-IF_LEFT
        self.viewport_y = self.window.height-IF_BOTTOM-IF_TOP
        #center map
        self.global_x = (self.mapset.width*self.tile_size-self.viewport_x+self.tile_size)//2
        self.global_y = (self.mapset.height*self.tile_size)//2-(self.viewport_y//2)+(self.tile_size//2)
        
        self.mouse_x = self.mouse_dx = 0
        self.mouse_y = self.mouse_dy = 0
    
    def _init_view(self):
        #step one tile
        self.steps = self.tile_size
        
        self.viewport_x = self.window.width-IF_RIGHT-IF_LEFT
        self.viewport_y = self.window.height-IF_BOTTOM-IF_TOP
        
        #center map when viewport is too large, else check if map still fills
        #whole viewport and if not adjust position accordingly
        self.center_x = False
        if self.mapset.width*self.tile_size < self.viewport_x:
            self.center_x = True
            self.global_x = (self.mapset.width*self.tile_size)//2-(self.viewport_x//2)
        elif self.global_x > self.tile_size*self.mapset.width-self.viewport_x:
            self.global_x = self.tile_size*self.mapset.width-self.viewport_x
        elif self.global_x < 0:
            self.global_x = 0
        
        self.center_y = False
        if self.mapset.height*self.tile_size < self.viewport_y:
            self.center_y = True
            self.global_y = (self.mapset.height*self.tile_size)//2-(self.viewport_y//2)
        elif self.global_y > self.tile_size*self.mapset.height-self.viewport_y:
            self.global_y = self.tile_size*self.mapset.height-self.viewport_y
        elif self.global_y < 0:
            self.global_y = 0
        
        #drawn tiles
        self.tiles_x = min((self.viewport_x//self.tile_size)+2, self.mapset.width)
        self.tiles_y = min((self.viewport_y//self.tile_size)+2, self.mapset.height)
        
        #undrawn map size
        self.undrawn_x = self.tile_size*(self.mapset.width-self.tiles_x)
        self.undrawn_y = self.tile_size*(self.mapset.height-self.tiles_y)
        #size of full undrawn steps
        self.undrawn_steps_x = self.steps*(self.undrawn_x//self.steps)
        self.undrawn_steps_y = self.steps*(self.undrawn_y//self.steps)
        
        self.vertex_list = [[] for i in xrange(self.tiles_y)]
        self.vl_objects = [[] for i in xrange(self.tiles_y+4)]
        self.batch = pyglet.graphics.Batch()
        
        self.view_x = 0
        self.view_y = 0
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
        
        for y in xrange(self.tiles_y-1, -1, -1):
            y1 = y*32+IF_BOTTOM
            y2 = y1+32
            for x in xrange(self.tiles_x-1, -1, -1):
                x1 = x*32+IF_LEFT
                x2 = x1+32
                tile = self.mapset.tiles[x-self.div_x, self.div_y-y]
                self.vertex_list[y].insert(0, self.batch.add(4, pyglet.gl.GL_QUADS, self.mapset.group,
                                    ('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
                                    ('t3f', tile.tex_coords),
                                    ('c4B', (255,255,255,255)*4)))
        
        vertices = []
        tex_coords = []
        count = 0
        for y in xrange(self.tiles_y-1, -6, -1):
            y1 = y*32+IF_BOTTOM
            for x in xrange(self.tiles_x+5-1, -1, -1):
                o = self.mapset.tunedobj.get((x-self.div_x, self.div_y-y), None)
                if(o is not None):
                    for obj in o:
                        x1 = x*32+IF_LEFT-obj.width+32
                        x2 = x1+obj.width
                        y2 = y1+obj.height
                        vertices.extend([x1, y1, x2, y1, x2, y2, x1, y2])
                        tex_coords.extend(obj.tex_coords)
                        count+=4
        
        self.vl_objects = self.batch.add(count, pyglet.gl.GL_QUADS,
                        self.mapset.group_obj,
                        ('v2i', vertices),
                        ('t3f', tex_coords),
                        ('c4B', (255,255,255,255)*count))
                
        self.view_x = mod_x-self.steps-(self.tile_size-32)//4
        self.view_y = mod_y-self.steps-((self.tile_size-32)*3)//2
    
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
        self.label.draw()
    
    def _move(self, dx, dy):
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
        
        retex = False
        
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
            for y in xrange(self.tiles_y-1, -1, -1):
                for x in xrange(self.tiles_x-1, -1, -1):
                    tile = self.mapset.tiles[x-self.div_x, self.div_y-y]
                    self.vertex_list[y][x].tex_coords = tile.tex_coords
            vertices = []
            tex_coords = []
            count = 0
            for y in xrange(self.tiles_y-1, -6, -1):
                y1 = y*32+IF_BOTTOM
                for x in xrange(self.tiles_x+5-1, -1, -1):
                    o = self.mapset.tunedobj.get((x-self.div_x, self.div_y-y), None)
                    if(o is not None):
                        for obj in o:
                            x1 = x*32+IF_LEFT-obj.width+32
                            x2 = x1+obj.width
                            y2 = y1+obj.height
                            tex_coords.extend(obj.tex_coords)
                            vertices.extend([x1, y1, x2, y1, x2, y2, x1, y2])
                            count+=4
            self.vl_objects.resize(count)
            self.vl_objects.tex_coords = tex_coords
            self.vl_objects.vertices = vertices
            self.vl_objects.colors = (255,255,255,255)*count
        
        if not self.center_x:
            self.view_x = mod_x-self.steps-(self.tile_size-32)//4
            self.global_x = self.steps-new_global_x
        if not self.center_y:
            self.view_y = mod_y-self.steps-((self.tile_size-32)*3)//2
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
            elif self.window.keys[pyglet.window.key.PLUS] and \
                 self.tile_size < 32:
                self.tile_size+=8
                self._init_view()
            elif self.window.keys[pyglet.window.key.MINUS] and \
                 self.tile_size > 16:
                self.tile_size-=8
                self._init_view()
        except KeyError:
            pass
        if self.dx or self.dy:
            self._move(self.dx, self.dy)
            self.dx = 0
            self.dy = 0
        #mouse position:
        if self.mouse_x != self.mouse_dx or self.mouse_y != self.mouse_dy:
            self.mouse_x = self.mouse_dx
            self.mouse_y = self.mouse_dy
            x = (self.mouse_x-IF_LEFT-self.view_x
                -(self.tile_size-32)//4)//self.tile_size
            y = (self.mouse_y-IF_BOTTOM-self.view_y
                -((self.tile_size-32)*3)//2)//self.tile_size
            self.label.text = "%03d %03d"%(x-self.div_x, self.div_y-y)
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.dx += dx
        self.dy += dy
        self.mouse_dx = x
        self.mouse_dy = y
        return pyglet.event.EVENT_HANDLED
    
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_dx = x
        self.mouse_dy = y
        return pyglet.event.EVENT_HANDLED
    
    def on_resize(self, width, height):
        self._init_view()
    
    def animate_water(self, dt):
        for y in xrange(self.tiles_y):
            for x in xrange(self.tiles_x):
                tile = self.mapset.tiles[x-self.div_x, self.div_y-y]
                if isinstance(tile, Animation):
                    self.vertex_list[y][x].tex_coords = tile.next_tex_coords

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(1024, 768, resizable=True, vsync=False )
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.fps = pyglet.clock.ClockDisplay()
        pyglet.clock.schedule(lambda dt: None)
    
    def on_draw(self):
        self.fps.draw()
    
    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.F11:
            self.set_fullscreen(fullscreen=not self.fullscreen)
        elif symbol == pyglet.window.key.P:
            pyglet.image.get_buffer_manager().get_color_buffer().save('screenshot.png')

class Interface(object):
    def __init__(self, window):
        self.window = window
    
    def on_mouse_motion(self, x, y, dx, dy):
        if IF_LEFT < x < (self.window.width-IF_RIGHT):
            pass
        else:
            return pyglet.event.EVENT_HANDLED
        if IF_BOTTOM < y < (self.window.height-IF_TOP):
            pass
        else:
            return pyglet.event.EVENT_HANDLED

class LoadScreen(object):
    def __init__(self, window):
        self.window = window
        self.label = pyglet.text.Label('',
                font_name="Linux Libertine",
                font_size=28,
                x=self.window.width-10, y=10,
                anchor_x='right', anchor_y='bottom')
        
        self.label.text = "PARSING MAP FILE..."
        h3m = json.loads(pyglet.resource.file("test.h3m").read())
        self.label.text = "PARSING MAP FILE..."
#        edge_map = [[] for i in xrange(len(loaded_map)+16)]
#        for num in xrange(len(edge_map)):
#            if num < 7 or num > len(edge_map)-8:
#                line = []
#                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(len(loaded_map[0])+18)])
#            elif num == 7:
#                line = []
#                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
#                line.append([-1, 16, 0, 0, 0, 0, 0])
#                line.extend([[-1, 20+i%4, 0, 0, 0, 0, 0] for i in xrange(len(loaded_map[0]))])
#                line.append([-1, 17, 0, 0, 0, 0, 0])
#                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
#            elif num == len(edge_map)-8:
#                line = []
#                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
#                line.append([-1, 19, 0, 0, 0, 0, 0])
#                line.extend([[-1, 28+i%4, 0, 0, 0, 0, 0] for i in xrange(len(loaded_map[0]))])
#                line.append([-1, 18, 0, 0, 0, 0, 0])
#                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
#            else:
#                line = []
#                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
#                line.append([-1, 32+num%4, 0, 0, 0, 0, 0])
#                line.extend(loaded_map[num-8])
#                line.append([-1, 24+num%4, 0, 0, 0, 0, 0])
#                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
#            edge_map[num] = line
        self.label.text = "INITIATING MAPSET..."
        
        mapset = MapSet(h3m["upper_terrain"], h3m["objects"], h3m["tunedobj"])
        self.label.text = "INITIATING MAPVIEW..."
        mapview = MapView(mapset, self.window)
        interface = Interface(self.window)
        self.window.pop_handlers()
        self.window.push_handlers(mapview)
        self.window.push_handlers(interface)
        self.window.push_handlers(self.window.keys)
        
if __name__ == '__main__':
    pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    window = Window()
    window.push_handlers(LoadScreen(window))
    img = pyglet.resource.image("data/cursors/cradvntr.def/0.png")
    window.set_mouse_cursor(pyglet.window.ImageMouseCursor(img, 0, 40))
    pyglet.app.run()
