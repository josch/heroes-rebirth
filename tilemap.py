from __future__ import division
from random import randint, choice
from itertools import chain, repeat
from logging import getLogger

from pyglet import gl
from pyglet import clock
from pyglet.event import EventDispatcher
from pyglet.resource import Loader
from pyglet.image import ImageGrid, TextureGrid, Animation
from pyglet.sprite import Sprite
from pyglet.graphics import Batch, TextureGroup

LOGGER = getLogger("defence.tilemap")
TILE_LOADER = Loader(["graphics/tiles"])

class TileLayerGroup(TextureGroup):
	def __init__(self, texture, translation=(0, 0), rotation=0):
		super(TileLayerGroup, self).__init__(texture)
		self.translation = translation
		self.rotation = rotation
	
	def set_state(self):
		super(TileLayerGroup, self).set_state()
		
		gl.glPushAttrib(gl.GL_COLOR_BUFFER_BIT)
		gl.glEnable(gl.GL_BLEND)
		gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
		
		x, y = self.translation
		
		gl.glPushMatrix()
		gl.glTranslatef(x, y, 0)
		gl.glRotatef(self.rotation, 0, 0, 1)
		
		#gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
		#gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
		#gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
		#gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
		#gl.glTexParameterfv(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BORDER_COLOR, (1, 1, 1, 1))
	
	def unset_state(self):
		super(TileLayerGroup, self).unset_state()
		gl.glPopMatrix()
		gl.glPopAttrib()
	
	def __eq__(self, other):
		return (super(TileLayerGroup, self).__eq__(other)
			and self.translation == other.translation
			and self.rotation == other.rotation)
	
	def __repr__(self):
		return '%s(id=%d, transformation=%s, rotation=%d)' % (
			self.__class__.__name__,
			self.texture.id,
			self.translation,
			self.rotation)


class Animator(object):
	def __init__(self, delay):
		self.delay = delay
		self.paused = False
		self.tiles = set()
	
	def animate(self, dt):
		for tile in self.tiles:
			pass

class Tileset(object):
	def __init__(self, graphic, tilesize=16, framedelay=1):		
		rows, columns = graphic.height // tilesize, graphic.width // tilesize
		grid = TextureGrid(ImageGrid(graphic, rows, columns))
		
		self.texture = grid.texture
		
		self.frames = rows
		self.animated = self.frames > 1
		self.framedelay = framedelay
		
		self.subtiles = [grid[(0, x):(grid.rows, x+1)] for x in xrange(grid.columns)]
		self.texcoords = [[frame.tex_coords for frame in subtile] for subtile in self.subtiles]
	
	def __getitem__(self, index):
		return self.subtiles[index]

class Tile(object):
	def __init__(self, tileset, frame=0):
		self.tileset = tileset
		self.frame = frame
		
		#self.subtiles = (2, 3, 0, 1)
		self.subtiles = [randint(0, 3) for x in xrange(4)]
		self.subtiles = [randint(12, 15) for x in xrange(4)]
	
	def vertices(self, offset=(0, 0)):
		"""x, y = offset
		
		vertices = (
			x,   y,   x+1, y,   x+1, y+1, x,   y+1,
			x+1, y,   x+2, y,   x+2, y+1, x+1, y+1,
			x,   y+1, x+1, y+1, x+1, y+2, x,   y+2,
			x+1, y+1, x+2, y+1, x+2, y+2, x+1, y+2)"""
		
		vertices = (
			0, 0, 1, 0, 1, 1, 0, 1,
			1, 0, 2, 0, 2, 1, 1, 1,
			0, 1, 1, 1, 1, 2, 0, 2,
			1, 1, 2, 1, 2, 2, 1, 2)
		
		"""vertices = (
			0, 0, 0, 1, 0, 3, 1, 1, 5, 0, 1, 0,
			1, 0, 1, 2, 0, 5, 2, 1, 2, 1, 1, 4,
			0, 1, 9, 1, 1, 0, 1, 2, 1, 0, 2, 5,
			1, 1, 4, 2, 1, 3, 2, 2, 0, 1, 2, 1)
		
		offset = list(offset)
		offset.append(0)"""
		
		return ((coord * 16) + offset[i%2] for i, coord in enumerate(vertices))
	
	@property
	def texcoords(self):
		for subtile in self.subtiles:
			for coord in self.tileset.texcoords[subtile][self.frame]:
				yield coord
	
	@property
	def colours(self):
		return repeat(255, 4*4*4)

tilesets = {
	"#": Tileset(TILE_LOADER.image("grass.png")),
	"~": Tileset(TILE_LOADER.image("water.png"))}

class TileLayer(EventDispatcher):
	def __init__(self, tileset, tiles):
		self.tileset = tileset
		self._tiles = tiles

	def __getitem__(self, coords):
		x, y = coords
		return self._tiles[y][x]
	
	def __len__(self):
		return len(list(self.tiles))
	
	def animate(self, dt):
		for tile in self.tiles:
			tile.frame += 1# random.randint(0, 2)
			if tile.frame >= tile.tileset.frames:
				tile.frame = 0
		
		self.dispatch_event("on_animate")
		
		"""return
			start = index*(3*4*4)
			end = (index+1)*(3*4*4)
			
			self.tempcoords[start:end]=tile.texcoords
			#self.vlists[0].tex_coords[start:end]=tile.texcoords
		self.vlists[0].tex_coords=self.tempcoords"""
	
	@property
	def tiles(self):
		for row in self._tiles:
			for tile in row:
				if tile is not None:
					yield tile
	
	def coordtiles(self):
		for y, row in enumerate(self.tilelayer):
			for x, tile in enumerate(row):
				yield (x, y), tile
TileLayer.register_event_type('on_animate')

class LayerView(object):
	def __init__(self, mapview, tilelayer):
		self.tilelayer = tilelayer
		self.group = TileLayerGroup(self.tilelayer.tileset.texture)
		self.mapview = mapview
		self.vlist = None
		
		def rotate(dt):
			self.group.rotation += 0.5
		
		self.tilelayer.push_handlers(self)
		#clock.schedule_interval(rotate, 0.01)
	
	def refresh(self):
		if self.vlist is not None:
			self.vlist.delete()
		
		vertices = []
		for y, row in enumerate(self.tilelayer._tiles):
			for x, tile in enumerate(row):
				if tile is not None:
					vertices.extend(tile.vertices((x*32, y*32)))
		
		texcoords = list(chain(*(tile.texcoords for tile in self.tilelayer.tiles)))
		colours = list(chain(*(tile.colours for tile in self.tilelayer.tiles)))
		
		self.vlist = self.mapview.batch.add(
			len(self.tilelayer)*16, gl.GL_QUADS, self.group,
			('v2i', vertices),
			('t3f', texcoords),
			('c4B', colours))
	
	def on_animate(self):
		def tex():
			for tile in self.tilelayer.tiles:
				for texcoord in tile.texcoords:
					yield texcoord
		
		self.vlist.tex_coords = list(tex())

class TileMap(object):
	def __init__(self, layers):
		self.layers = [
			TileLayer(tilesets["#"], [[Tile(tilesets["#"]) for x in xrange(20)] for y in xrange(15)]),
			TileLayer(tilesets["~"], [[choice((Tile(tilesets["~"]), None)) for x in xrange(20)] for y in xrange(15)])]
	
	def animate(self, dt):
		for layer in self.layers:
			if layer.tileset.animated:
				layer.animate(dt)

class MapView(object):
	def __init__(self, tilemap):
		self.tilemap = tilemap
		self.batch = Batch()
		
		self.layerviews = [LayerView(self, layer) for layer in tilemap.layers]
		
		self.refresh()
	
	def refresh(self):
		for layerview in self.layerviews:
			layerview.refresh()
	
	def draw(self):
		self.batch.draw()
	
	def move(self, movement):
		dx, dy = movement
		for layerview in self.layerviews:
			x, y = layerview.group.translation
			layerview.group.translation = (x+dx, y+dy)

if __name__ == "__main__":
	import pyglet
	
	window = pyglet.window.Window(640, 480, "Defence", vsync=False)
	tmap = TileMap(None)
	view = MapView(tmap)
	
	fps = pyglet.clock.ClockDisplay()
	
	@window.event
	def on_draw():
		window.clear()
		view.draw()
		fps.draw()
	
	@window.event
	def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
		view.move((dx, dy))
	
	pyglet.clock.schedule_interval(tmap.animate, 1/10.0)
	pyglet.clock.schedule(lambda dt: None)
	pyglet.app.run()

