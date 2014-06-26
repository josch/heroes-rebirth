#!/usr/bin/python
"""
    homm3hmtest
    
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

def extract(filename):
    h3m_data = gzip.open(filename)
    map_data = {}
    #read general info
    (map_data["version"], ) = struct.unpack("<I", h3m_data.read(4))
    if map_data["version"] == 0x1C:
        h3m_data.read(1)
        (size,) = struct.unpack("<I", h3m_data.read(4))
        print filename, size
    
def main(args):
    for arg in args[1:]:
        extract(arg)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
