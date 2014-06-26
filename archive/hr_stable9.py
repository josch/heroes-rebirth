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

import pyglet, re
from ctypes import create_string_buffer, memmove
import itertools

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import demjson as json
        json.loads = json.decode
        json.dumps = json.encode

IF_BOTTOM = 0#48
IF_RIGHT = 0#200
IF_TOP = IF_LEFT = 0#8

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
        return hash((self.order, self.texture.target, self.texture.id,
               self.parent))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
            self.order == other.order and
            self.texture.target == other.texture.target and
            self.texture.id == other.texture.id and
            self.parent == self.parent)

    def __repr__(self):
        return '%s(id=%d)' % (self.__class__.__name__, self.order,
               self.texture.id)
        
    def __cmp__(self, other):
        if isinstance(other, OrderedTextureGroup):
            return cmp(self.order, other.order)
        return -1

class Animation(object):
    def __init__(self, tex_region, frames, flip_x=False, flip_y=False):
        self.texgroup = tex_region.group
        if flip_x or flip_y:
            self.tex = tex_region.get_transform(flip_x=flip_x, flip_y=flip_y)
        else:    
            self.tex = tex_region
        self.__frames = []
        for img in frames:
            data_pitch = abs(img._current_pitch)
            buf = create_string_buffer(len(img._current_data))
            memmove(buf, img._current_data, len(img._current_data))
            data = buf.raw
            rows = [data[i:i + abs(data_pitch)] for i in
                   xrange(len(img._current_data)-abs(data_pitch),
                   -1, -abs(data_pitch))]
            self.__frames.append(''.join(rows))
        self.__animation = 0
        self.width = self.tex.width
        self.height = self.tex.height
        self.__hash = hash(self.__frames[0])
    
    def next_frame(self):
        self.__animation = (self.__animation + 1) % len(self.__frames)
        return self.__frames[self.__animation]
    
    @property
    def tex_coords(self):
        return self.tex.tex_coords
    
    @property
    def group(self):
        return self.texgroup
    
    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        return self.__hash == other.__hash

class MapSet(object):
    def load_map_object(self, file, order=0):
        image = pyglet.image.load(None, file=pyglet.resource.file(file))
        try:
            texture_region = self.current_atlas.add(image)
        except pyglet.image.atlas.AllocatorException:
            self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
            texture_region = self.current_atlas.add(image)
        group = OrderedTextureGroup(order, self.current_atlas.texture)
        
        if group not in self.groups:
            self.groups.append(group)
        
        texture_region.group = self.groups.index(group)
        return texture_region

    def __init__(self, loaded_map, objects, tunedobj):
        self.width = len(loaded_map[0])
        self.height = len(loaded_map)
        
        self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
        
        self.groups = []
        
        self.__tiles = {}
        tile_textures = {}
        for y, line in enumerate(loaded_map):
            for x, tile in enumerate(line):
                if tile[0] == -1: #edge
                    if "edg" not in tile_textures.keys():
                        tile_textures["edg"] = [self.load_map_object('data/tiles/edg.def/%d.png'%i, 100) for i in xrange(36)]
                    self.__tiles[x,y] = [tile_textures["edg"][tile[1]]]
                elif tile[0] == 0: #dirt
                    if "dirttl" not in tile_textures.keys():
                        tile_textures["dirttl"] = [self.load_map_object('data/tiles/dirttl.def/%d.png'%i, 0) for i in xrange(46)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["dirttl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["dirttl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["dirttl"][tile[1]]]
                elif tile[0] == 1: #sand
                    if "sandtl" not in tile_textures.keys():
                        tile_textures["sandtl"] = [self.load_map_object('data/tiles/sandtl.def/%d.png'%i, 0) for i in xrange(24)]
                    self.__tiles[x,y] = [tile_textures["sandtl"][tile[1]]]
                elif tile[0] == 2: #grass
                    if "grastl" not in tile_textures.keys():
                        tile_textures["grastl"] = [self.load_map_object('data/tiles/grastl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["grastl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["grastl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["grastl"][tile[1]]]
                elif tile[0] == 3: #snow
                    if "snowtl" not in tile_textures.keys():
                        tile_textures["snowtl"] = [self.load_map_object('data/tiles/snowtl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["snowtl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["snowtl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["snowtl"][tile[1]]]
                elif tile[0] == 4: #swamp
                    if "swmptl" not in tile_textures.keys():
                        tile_textures["swmptl"] = [self.load_map_object('data/tiles/swmptl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["swmptl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["swmptl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["swmptl"][tile[1]]]
                elif tile[0] == 5: #rough
                    if "rougtl" not in tile_textures.keys():
                        tile_textures["rougtl"] = [self.load_map_object('data/tiles/rougtl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["rougtl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["rougtl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["rougtl"][tile[1]]]
                elif tile[0] == 7: #lava
                    if "lavatl" not in tile_textures.keys():
                        tile_textures["lavatl"] = [self.load_map_object('data/tiles/lavatl.def/%d.png'%i, 0) for i in xrange(79)]
                    flip_x = bool(tile[6] & 1)
                    flip_y = bool(tile[6] & 2)
                    if flip_x or flip_y:
                        new = tile_textures["lavatl"][tile[1]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["lavatl"][tile[1]].group
                        self.__tiles[x,y] = [new]
                    else:
                        self.__tiles[x,y] = [tile_textures["lavatl"][tile[1]]]
                elif tile[0] == 8: #water 12 anims
                    if "watrtl" not in tile_textures.keys():
                        textures = [self.load_map_object('data/tiles/watrtl.def/%d/0.png'%i, 0) for i in xrange(33)]
                        images = [[pyglet.image.load(None, file=pyglet.resource.file('data/tiles/watrtl.def/%d/%d.png'%(i,j))) for j in xrange(12)] for i in xrange(33)]
                        tile_textures["watrtl"] = {
                            (0,0):[Animation(texture, images[i]) for i, texture in enumerate(textures)],
                            (1,0):[Animation(texture, images[i], flip_x=True) for i, texture in enumerate(textures)],
                            (0,1):[Animation(texture, images[i], flip_y=True) for i, texture in enumerate(textures)],
                            (1,1):[Animation(texture, images[i], flip_x=True, flip_y=True) for i, texture in enumerate(textures)],
                        }
                    flip_x = (tile[6]>>0)&1
                    flip_y = (tile[6]>>1)&1
                    self.__tiles[x,y] = [tile_textures["watrtl"][flip_x, flip_y][tile[1]]]
                elif tile[0] == 9: #rock
                    if "rocktl" not in tile_textures.keys():
                        tile_textures["rocktl"] = [self.load_map_object('data/tiles/rocktl.def/%d.png'%i, 0) for i in xrange(48)]
                    self.__tiles[x,y] = [tile_textures["rocktl"][tile[1]]]
                else:
                    raise NotImplementedError
                
                if tile[2] == 0: #no river
                    pass
                elif tile[2] == 1: #clrrvr 12 anims
                    if "clrrvr" not in tile_textures.keys():
                        textures = [self.load_map_object('data/tiles/clrrvr.def/%d/0.png'%i, 1) for i in xrange(13)]
                        images = [[pyglet.image.load(None, file=pyglet.resource.file('data/tiles/clrrvr.def/%d/%d.png'%(i,j))) for j in xrange(12)] for i in xrange(13)]
                        tile_textures["clrrvr"] = {
                            (0,0):[Animation(texture, images[i]) for i, texture in enumerate(textures)],
                            (1,0):[Animation(texture, images[i], flip_x=True) for i, texture in enumerate(textures)],
                            (0,1):[Animation(texture, images[i], flip_y=True) for i, texture in enumerate(textures)],
                            (1,1):[Animation(texture, images[i], flip_x=True, flip_y=True) for i, texture in enumerate(textures)],
                        }
                    flip_x = (tile[6]>>2)&1
                    flip_y = (tile[6]>>3)&1
                    self.__tiles[x,y].append(tile_textures["clrrvr"][flip_x, flip_y][tile[3]])
                elif tile[2] == 2: #icyrvr
                    if "icyrvr" not in tile_textures.keys():
                        tile_textures["icyrvr"] = [self.load_map_object('data/tiles/icyrvr.def/%d.png'%i, 1) for i in xrange(13)]
                    flip_x = bool(tile[6] & 4)
                    flip_y = bool(tile[6] & 8)
                    if flip_x or flip_y:
                        new = tile_textures["icyrvr"][tile[3]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["icyrvr"][tile[3]].group
                        self.__tiles[x, y].append(new)
                    else:
                        self.__tiles[x, y].append(tile_textures["icyrvr"][tile[3]])
                elif tile[2] == 3: #mudrvr
                    if "mudrvr" not in tile_textures.keys():
                        textures = [self.load_map_object('data/tiles/mudrvr.def/%d/0.png'%i, 1) for i in xrange(13)]
                        images = [[pyglet.image.load(None, file=pyglet.resource.file('data/tiles/clrrvr.def/%d/%d.png'%(i,j))) for j in xrange(12)] for i in xrange(13)]
                        tile_textures["mudrvr"] = {
                            (0,0):[Animation(texture, images[i]) for i, texture in enumerate(textures)],
                            (1,0):[Animation(texture, images[i], flip_x=True) for i, texture in enumerate(textures)],
                            (0,1):[Animation(texture, images[i], flip_y=True) for i, texture in enumerate(textures)],
                            (1,1):[Animation(texture, images[i], flip_x=True, flip_y=True) for i, texture in enumerate(textures)],
                        }
                    flip_x = (tile[6]>>2)&1
                    flip_y = (tile[6]>>3)&1
                    self.__tiles[x,y].append(tile_textures["mudrvr"][flip_x, flip_y][tile[3]])
                elif tile[2] == 4: #lavrvr
                    if "lavrvr" not in tile_textures.keys():
                        textures = [self.load_map_object('data/tiles/lavrvr.def/%d/0.png'%i, 1) for i in xrange(13)]
                        images = [[pyglet.image.load(None, file=pyglet.resource.file('data/tiles/clrrvr.def/%d/%d.png'%(i,j))) for j in xrange(9)] for i in xrange(13)]
                        tile_textures["lavrvr"] = {
                            (0,0):[Animation(texture, images[i]) for i, texture in enumerate(textures)],
                            (1,0):[Animation(texture, images[i], flip_x=True) for i, texture in enumerate(textures)],
                            (0,1):[Animation(texture, images[i], flip_y=True) for i, texture in enumerate(textures)],
                            (1,1):[Animation(texture, images[i], flip_x=True, flip_y=True) for i, texture in enumerate(textures)],
                        }
                    flip_x = (tile[6]>>2)&1
                    flip_y = (tile[6]>>3)&1
                    self.__tiles[x,y].append(tile_textures["lavrvr"][flip_x, flip_y][tile[3]])
                else:
                    raise NotImplementedError, tile[2]
                
                if tile[4] == 0: #no road
                    pass
                elif tile[4] == 1: #dirtrd
                    if "dirtrd" not in tile_textures.keys():
                        tile_textures["dirtrd"] = [self.load_map_object('data/tiles/dirtrd.def/%d.png'%i, 1) for i in xrange(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["dirtrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["dirtrd"][tile[5]].group
                        self.__tiles[x, y].append(new)
                    else:
                        self.__tiles[x, y].append(tile_textures["dirtrd"][tile[5]])
                elif tile[4] == 2: #gravrd
                    if "gravrd" not in tile_textures.keys():
                        tile_textures["gravrd"] = [self.load_map_object('data/tiles/gravrd.def/%d.png'%i, 1) for i in xrange(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["gravrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["gravrd"][tile[5]].group
                        self.__tiles[x, y].append(new)
                    else:
                        self.__tiles[x, y].append(tile_textures["gravrd"][tile[5]])
                elif tile[4] == 3: #cobbrd
                    if "cobbrd" not in tile_textures.keys():
                        tile_textures["cobbrd"] = [self.load_map_object('data/tiles/cobbrd.def/%d.png'%i, 1) for i in xrange(17)]
                    flip_x = bool(tile[6] & 16)
                    flip_y = bool(tile[6] & 32)
                    if flip_x or flip_y:
                        new = tile_textures["cobbrd"][tile[5]].get_transform(flip_x=flip_x, flip_y=flip_y)
                        new.group = tile_textures["cobbrd"][tile[5]].group
                        self.__tiles[x, y].append(new)
                    else:
                        self.__tiles[x, y].append(tile_textures["cobbrd"][tile[5]])
                else:
                    raise NotImplementedError, tile[4]
        
        images = []
        for order, obj in enumerate(objects):
            imgs = []
            i = 0
            while 1:
                imgs.append(pyglet.image.load(None, file=pyglet.resource.file("data/map_objects/" + obj["filename"] + "/%d.png"%i)))
                i += 1
                if "data/map_objects/" + obj["filename"] + "/%d.png" % i not in pyglet.resource._default_loader._index.keys():
                    break;
            images.append((imgs, order))
        
        self.objects = []
        for imgs in sorted(images, key=lambda i:i[0][0].height, reverse=True):
            try:
                texture = self.current_atlas.add(imgs[0][0])
            except pyglet.image.atlas.AllocatorException:
                self.current_atlas = pyglet.image.atlas.TextureAtlas(1024, 1024)
                print "atlas"
                texture = self.current_atlas.add(imgs[0][0])
            group = OrderedTextureGroup(2, self.current_atlas.texture)
            if group not in self.groups:
                self.groups.append(group)
            group = self.groups.index(group)
            texture.group = group
            self.objects.append((Animation(texture, imgs[0]), imgs[1]))
        
        self.objects = [i[0] for i in sorted(self.objects, key=lambda i:i[1])]
        
        self.tunedobj = {}
        for obj in [i for i in tunedobj if i["z"]==0]:
            self.__tiles[obj["x"] + 9,obj["y"] + 8].append(self.objects[obj["id"]])
    
    def get_tiles(self, tiles_x, tiles_y, div_x, div_y):
        for y in xrange(tiles_y - 1, -6, -1):
            y1 = y * 32 + IF_BOTTOM
            for x in xrange(tiles_x + 5 - 1, -1, -1):
                for obj in self.__tiles.get((x - div_x, div_y - y), []):
                    x1 = x * 32 + IF_LEFT - obj.width + 32
                    x2 = x1 + obj.width
                    y2 = y1 + obj.height
                    yield obj, [x1, y1, x2, y1, x2, y2, x1, y2]


class MapView(object):
    def __init__(self, mapset, window):
        self.window = window
        self.mapset = mapset
        self._first_time_init()
        self._init_view()
        # mouse position
        self.label = pyglet.text.Label('',
                font_name="",
                font_size=36,
                bold=True,
                color=(128, 128, 128, 128),
                x=self.window.width - 10, y=0,
                anchor_x='right', anchor_y='bottom')
        pyglet.clock.schedule_interval(self.animate_water, 1/6.0)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
    
    def _first_time_init(self):
        self.tile_size = 32
        # size of the viewport
        self.vp_width = self.window.width-IF_RIGHT-IF_LEFT
        self.vp_height = self.window.height-IF_BOTTOM-IF_TOP
        # center map
        self.x = (self.mapset.width * self.tile_size - self.vp_width + 
                  self.tile_size) // 2
        self.y = (self.mapset.height * self.tile_size - self.vp_height + 
                  self.tile_size) // 2
        self.mouse_x = self.mouse_dx = 0
        self.mouse_y = self.mouse_dy = 0
    
    def _init_view(self):
        # initiate new batch
        self.batch = pyglet.graphics.Batch()
        # initiate new vertex list
        self.vl_objects = [None for value in self.mapset.groups]
        # size of the viewport
        self.vp_width = self.window.width - IF_RIGHT - IF_LEFT
        self.vp_height = self.window.height - IF_BOTTOM - IF_TOP
        # center map when viewport is too large, else check if map still fills
        # whole viewport and if not adjust position accordingly
        self.center_x = False
        if self.mapset.width * self.tile_size < self.vp_width:
            # center the map in x direction
            self.center_x = True
            self.x = (self.mapset.width * self.tile_size - self.vp_width) // 2
        elif self.x > self.tile_size * self.mapset.width - self.vp_width:
            # move map back to the right
            self.x = self.tile_size * self.mapset.width - self.vp_width
        elif self.x < 0:
            # move map to the left
            self.x = 0
        self.center_y = False
        if self.mapset.height * self.tile_size < self.vp_height:
            # center the map in y direction
            self.center_y = True
            self.y = (self.mapset.height * self.tile_size -
                      self.vp_height) // 2
        elif self.y > self.tile_size * self.mapset.height - self.vp_height:
            # move map up
            self.y = self.tile_size * self.mapset.height - self.vp_height
        elif self.y < 0:
            # move map down
            self.y = 0
        # tiles to be drawn with the current viewport size
        self.tiles_x = min((self.vp_width // self.tile_size) + 2,
                           self.mapset.width)
        self.tiles_y = min((self.vp_height // self.tile_size) + 2,
                           self.mapset.height)
        # undrawn map size in pixels
        self.undrawn_x = self.tile_size * (self.mapset.width - self.tiles_x)
        self.undrawn_y = self.tile_size * (self.mapset.height - self.tiles_y)
        # reset mouse or keyboard movement
        self.dx = 0
        self.dy = 0
        # calculate modulo pixel position of the map
        if self.x - self.tile_size > self.undrawn_x:
            # dont go right beyond map borders
            mod_x = self.tile_size - self.x + self.undrawn_x
        elif self.x > 0:
            # calculate modulo of current position and tile_size
            mod_x = (self.tile_size - self.x) % self.tile_size
        else:
            # dont go left beyond map borders
            mod_x = self.tile_size - self.x
        if self.y - self.tile_size > self.undrawn_y:
            # dont go up beyond map borders
            mod_y = self.tile_size - self.y + self.undrawn_y
        elif self.y > 0:
            # calculate modulo of current position and tile_size
            mod_y = (self.tile_size - self.y) % self.tile_size
        else:
            # dont go down beyond map borders
            mod_y = self.tile_size - self.y
        # calculate tile position of the map, turn y coordinates upside down
        self.div_x = (self.tile_size - self.x - mod_x) // self.tile_size
        self.div_y = (self.tile_size - self.y - mod_y) // self.tile_size + \
                     self.mapset.height - 1
        # update vertex lists with the gathered information
        self.update_vertex_lists()
        # update current current position that is to be glTranslated
        # XXX: dont ask me why i have to add 1/4 and 3/2 but when i do not
        #      there are black borders when zooming out
        #      plz explain wtf is going on there
        self.view_x = mod_x - self.tile_size - (self.tile_size - 32) // 4
        self.view_y = mod_y - self.tile_size - ((self.tile_size - 32) * 3) // 2
    
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
        # new map position
        new_x = self.x - dx
        new_y = self.y - dy
        # only update textures and vertices when necessary
        retex = False
        # if x or y jump is too big, adjust new position accordingly
        if new_x < 0:
            # move map to the left
            new_x = 0
            retex = True
        if new_x > self.tile_size * self.mapset.width - self.vp_width:
            # move map to the right
            new_x = self.tile_size * self.mapset.width - self.vp_width
            retex = True
        if new_y < 0:
            # move map down
            new_y = 0
            retex = True
        if new_y > self.tile_size * self.mapset.height - self.vp_height:
            # move map up
            new_y = self.tile_size * self.mapset.height - self.vp_height
            retex = True
        # find out how many steps and pixels we have to move and wether we have
        # to retex
        if new_x - self.tile_size > self.undrawn_x:
            # we are at the right border
            mod_x = self.tile_size - new_x + self.undrawn_x
            # only retex if the last position was not at the border
            if self.x - self.tile_size <= self.undrawn_x:
                retex = True
        elif new_x > 0:
            # normal movement: calculate the amount of steps and the modulo
            div_x, mod_x = divmod(self.tile_size - new_x, self.tile_size)
            # only retex if the number of moved steps is not equal to last
            if div_x != (self.tile_size - self.x) // self.tile_size:
                retex = True
        else:
            # we are at the left border
            mod_x = self.tile_size - new_x
        if new_y - self.tile_size > self.undrawn_y:
            # we are at the top
            mod_y = self.tile_size - new_y + self.undrawn_y
            # only retex if the last position was not at the border
            if self.y - self.tile_size <= self.undrawn_y:
                retex = True
        elif new_y > 0:
            # normal movement: calculate the amount of steps and the modulo
            div_y, mod_y = divmod(self.tile_size - new_y, self.tile_size)
            # only retex if the number of moved steps is not equal to last
            if div_y != (self.tile_size - self.y) // self.tile_size:
                retex = True
        else:
            # we are at the bottom
            mod_y = self.tile_size - new_y
        # if we have to update vertices and textures
        if retex:
            # calculate the current position on the tilemap
            self.div_x = (self.tile_size - new_x - mod_x) // \
                         self.tile_size
            self.div_y = (self.tile_size - new_y - mod_y) // \
                         self.tile_size + self.mapset.height - 1
            self.update_vertex_lists()
        # update position if not centered
        # XXX: dont ask me why i have to add 1/4 and 3/2 but when i do not
        #      there are black borders when zooming out
        #      plz explain wtf is going on there
        if not self.center_x:
            self.view_x = mod_x-self.tile_size-(self.tile_size-32)//4
            self.x = new_x
        if not self.center_y:
            self.view_y = mod_y-self.tile_size-((self.tile_size-32)*3)//2
            self.y = new_y
    
    def update_vertex_lists(self):
        # initiate lists of vertex lists, vertices, texture coords, vertices
        # counts and map objects for each group
        vertices = [[] for value in self.mapset.groups]
        tex_coords = [[] for value in self.mapset.groups]
        count = [0 for value in self.mapset.groups]
        self.cur_objects = [[] for value in self.mapset.groups]
        # for each tile in the viewport, update the list of the specific group
        for obj, coords in self.mapset.get_tiles(self.tiles_x, self.tiles_y,
                                                 self.div_x, self.div_y):
            tex_coords[obj.group].extend(obj.tex_coords)
            vertices[obj.group].extend(coords)
            count[obj.group]+=4
            if isinstance(obj, Animation):
                self.cur_objects[obj.group].append(obj)
        for i, group in enumerate(self.mapset.groups):
            if count[i] == 0:
                if self.vl_objects[i] is None:
                    # let the vertex list be None
                    pass
                else:
                    # there was a vertex list but now no more - delete it
                    self.vl_objects[i].delete()
                    self.vl_objects[i] = None
            else:
                if self.vl_objects[i] is None:
                    # there was no vertex list but ther now is one - create it
                    self.vl_objects[i] = self.batch.add(count[i],
                            pyglet.gl.GL_QUADS,
                            group,
                            ('v2i', vertices[i]),
                            ('t3f', tex_coords[i]),
                            ('c4B', (255,255,255,255)*count[i]))
                else:
                    # there already is a vertex list - resize and refill
                    self.vl_objects[i].resize(count[i])
                    self.vl_objects[i].tex_coords = tex_coords[i]
                    self.vl_objects[i].vertices = vertices[i]
                    self.vl_objects[i].colors = (255,255,255,255)*count[i]
            # make object list unique
            self.cur_objects[i] = list(set(self.cur_objects[i]))
    
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
        # mouse position:
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
        for i, group in enumerate(self.mapset.groups):
            if len(self.cur_objects[i]) > 0:
                pyglet.gl.glBindTexture(self.cur_objects[i][0].tex.target,
                                        self.cur_objects[i][0].tex.id)
                for obj in self.cur_objects[i]:
                    pyglet.gl.glTexSubImage2D(obj.tex.owner.target,
                            obj.tex.owner.level,
                            obj.tex.x, obj.tex.y,
                            obj.tex.width, obj.tex.height,
                            pyglet.gl.GL_RGBA, pyglet.gl.GL_UNSIGNED_BYTE,
                            obj.next_frame())

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(1280, 1024, resizable=True, vsync=False)
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
            pyglet.image.get_buffer_manager().get_color_buffer().save(
                'screenshot.png', encoder=PNGRGBEncoder())

class PNGRGBEncoder(pyglet.image.codecs.ImageEncoder):
    def encode(self, image, file, filename):
        import Image
        image = image.get_image_data()
        format = image.format
        pitch = -(image.width * len(format))
        pil_image = Image.fromstring(
            format, (image.width, image.height), image.get_data(format, pitch))
        try:
            #.convert('P', palette=Image.WEB)
            pil_image.convert("RGB").save(file)
        except Exception, e:
            raise ImageEncodeException(e)


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
        edge_map = [[] for i in xrange(len(h3m["upper_terrain"])+16)]
        for num in xrange(len(edge_map)):
            if num < 7 or num > len(edge_map)-8:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(len(h3m["upper_terrain"][0])+18)])
            elif num == 7:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
                line.append([-1, 16, 0, 0, 0, 0, 0])
                line.extend([[-1, 20+i%4, 0, 0, 0, 0, 0] for i in xrange(len(h3m["upper_terrain"][0]))])
                line.append([-1, 17, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            elif num == len(edge_map)-8:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
                line.append([-1, 19, 0, 0, 0, 0, 0])
                line.extend([[-1, 28+i%4, 0, 0, 0, 0, 0] for i in xrange(len(h3m["upper_terrain"][0]))])
                line.append([-1, 18, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            else:
                line = []
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
                line.append([-1, 32+num%4, 0, 0, 0, 0, 0])
                line.extend(h3m["upper_terrain"][num-8])
                line.append([-1, 24+num%4, 0, 0, 0, 0, 0])
                line.extend([[-1, 0+(i-1)%4+4*(num%4), 0, 0, 0, 0, 0] for i in xrange(8)])
            edge_map[num] = line
        h3m["upper_terrain"] = edge_map
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
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA,
        pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    window = Window()
    window.push_handlers(LoadScreen(window))
    img = pyglet.resource.image("data/cursors/cradvntr.def/0.png")
    window.set_mouse_cursor(pyglet.window.ImageMouseCursor(img, 0, 40))
    pyglet.app.run()
