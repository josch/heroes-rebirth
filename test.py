#!/usr/bin/env python

import pyglet

atlas1 = pyglet.image.atlas.TextureAtlas(1024, 1024)
atlas2 = pyglet.image.atlas.TextureAtlas(1024, 1024)
atlas3 = pyglet.image.atlas.TextureAtlas(1024, 1024)

texture_group1 = pyglet.graphics.TextureGroup(atlas1.texture)
texture_group2 = pyglet.graphics.TextureGroup(atlas2.texture)
texture_group3 = pyglet.graphics.TextureGroup(atlas3.texture)

tile1 = atlas1.add(pyglet.image.load(None, file=pyglet.resource.file('test.png')))
tile2 = atlas2.add(pyglet.image.load(None, file=pyglet.resource.file('test.png')))
tile3 = atlas3.add(pyglet.image.load(None, file=pyglet.resource.file('test.png')))

tile2.blit_into(pyglet.image.load(None, file=pyglet.resource.file('test2.png')), 0, 0, 0)

batch = pyglet.graphics.Batch()
vertex_list = []

window = pyglet.window.Window(800, 600, vsync=False)
fps = pyglet.clock.ClockDisplay()

@window.event
def on_draw():
    pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT)
    batch.draw()
    fps.draw()

pyglet.clock.schedule(lambda dt: None)

def add_one(dt):
    vertex_list.append(batch.add(4, pyglet.gl.GL_QUADS, texture_group1,
        ('v2i', [0, 0, 32, 0, 32, 32, 0, 32]),
        ('t3f', tile1.tex_coords),
        ('c4B', (255,255,255,255)*4)))

def add_two(dt):
    vertex_list.append(batch.add(4, pyglet.gl.GL_QUADS, texture_group2,
        ('v2i', [8, 8, 40, 8, 40, 40, 8, 40]),
        ('t3f', tile2.tex_coords),
        ('c4B', (255,255,255,255)*4)))

def add_three(dt):
    vertex_list.append(batch.add(4, pyglet.gl.GL_QUADS, texture_group3,
        ('v2i', [16, 16, 48, 16, 48, 48, 16, 48]),
        ('t3f', tile3.tex_coords),
        ('c4B', (255,255,255,255)*4)))

pyglet.clock.schedule_once(add_one, 4.0)
pyglet.clock.schedule_once(add_two, 8.0)
pyglet.clock.schedule_once(add_three, 12.0)

pyglet.app.run()
