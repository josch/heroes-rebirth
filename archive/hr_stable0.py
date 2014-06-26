#!/usr/bin/python
"""
    homm3h3mview
    
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

import gzip, os
import struct
import sys
import pygame
from pygame.locals import *

class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, tile_seq, x, y, flip_x, flip_y):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        try:
            if tile_type == 8: #water
                image = pygame.image.load("/home/josch/fheroes3/tests/69 tiles/3229 Watrtl.def/watrtl%02d.pcx"%(tile_seq+1))
            elif tile_type == 2: #grass
                print tile_seq,
                path = "/home/josch/fheroes3/tests/69 tiles/3221 GRASTL.def/tgrs%03d.pcx"
                if tile_seq == 20:
                    image = pygame.image.load(path%0)
                elif tile_seq == 21:
                    image = pygame.image.load(path%1)
                elif tile_seq == 22:
                    image = pygame.image.load(path%2)
                elif tile_seq == 23:
                    image = pygame.image.load(path%3)
                elif tile_seq == 24:
                    image = pygame.image.load(path%10)
                elif tile_seq == 25:
                    image = pygame.image.load(path%11)
                elif tile_seq == 26:
                    image = pygame.image.load(path%12)
                elif tile_seq == 27:
                    image = pygame.image.load(path%13)
                elif tile_seq == 28:
                    image = pygame.image.load(path%20)
                elif tile_seq == 29:
                    image = pygame.image.load(path%21)
                elif tile_seq == 30:
                    image = pygame.image.load(path%22)
                elif tile_seq == 31:
                    image = pygame.image.load(path%23)
                elif tile_seq == 32:
                    image = pygame.image.load(path%30)
                elif tile_seq == 33:
                    image = pygame.image.load(path%31)
                elif tile_seq == 34:
                    image = pygame.image.load(path%32)
                elif tile_seq == 35:
                    image = pygame.image.load(path%33)
                else:
                    raise Exception
        except:
            image = pygame.image.load("/home/josch/fheroes3/tests/69 tiles/3999 Tshre.def/Tshre10.pcx")
        image = image.convert()
        if flip_x or flip_y:
            image = pygame.transform.flip(image, flip_x, flip_y)
        self.image = image
        self.rect = image.get_rect()
        self.rect.topleft = (32*x,32*y)

def extract(filename):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Heroes Rebirth')
    pygame.mouse.set_visible(1)
    clock = pygame.time.Clock()
    
    
    h3m_data = gzip.open(filename)
    h3m_data.seek(5)
    (map_size,) = struct.unpack("i", h3m_data.read(4))
    h3m_data.seek(390)
    tiles = []
    for i in xrange(map_size*map_size):
        x = i%map_size
        y = (i-x)/map_size
        tile = struct.unpack("7B", h3m_data.read(7))
        flip_x = tile[6] & 0x1
        flip_y = tile[6] & 0x2
        tile = Tile(tile[0], tile[1], x, y, flip_x, flip_y)
        tiles.append(tile)
    
    allsprites = pygame.sprite.RenderPlain(tiles)

    while 1:
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return
        allsprites.draw(screen)
        pygame.display.flip()
        clock.tick(25)
    
def main(args):
    if len(args) != 2:
        print 'usage: %s file' % args[0]
        return 2
    extract(args[1])

if __name__ == '__main__':
    sys.exit(main(sys.argv))
