# coding=utf-8

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Men of War MDL importer for Blender
# Script Copyright (C) by Björn Martins Paz

from __future__ import print_function

import struct
import math
from itertools import repeat

from anm_frame import ANM_FRAME
from anm_frame_event import ANM_FRAME_EVENT
from anm_frame_position import ANM_FRAME_POSITION
from anm_frame_quaternion import ANM_FRAME_QUATERNION

# constants
ANMMAGICK = b"EANM"
HEADER_ID = 0x00060000

FRAME_TYPE_POSITION = 1
FRAME_TYPE_QUATERNION = 2
FRAME_TYPE_INVERTED = 4
FRAME_TYPE_UNKOWN = 8
FRAME_TYPE_UNKOWN2= 16
FRAME_TYPE_VERTICES = 32
SUPPORTED_ENTRY = [b"FRMS", b"BMAP", b"FRM2"]

class ANM:
    def __init__(self, path):
        self.path = path
        self.duration = 0
        self.entities = []
        self.keyframes = []

        self.open()

    def open(self):
        with open(self.path, "rb") as f:
            # read header
            magick, = struct.unpack("4s", f.read(4))
            if magick != ANMMAGICK:
                raise Exception("Unsupported format: %s" % magick)
            header_id, = struct.unpack("<I", f.read(4))
            print("Found header ID:", hex(header_id))
            if header_id != HEADER_ID:
                raise Exception("Unsuported header ID")

            # process entries
            while True:
                px = 0; py = 0; pz = 0
                rx = 0; ry = 0; rz = 0

                try:
                    entry, = struct.unpack("4s", f.read(4))
                except struct.error:
                    return

                print("Found entry %s at %s" % (entry, hex(f.tell())))
                if not(entry in SUPPORTED_ENTRY):
                    raise Exception("Unsupported entry type: %s" % entry)
                
                if entry == SUPPORTED_ENTRY[0]:  #FRMS
                    # read duration (time) of the animation
                    self.duration, = struct.unpack("<I", f.read(4))
                    print("Animation time:", self.duration)

                if entry == SUPPORTED_ENTRY[1]:  #BMAP
                    # read total number of entities involved in this animation
                    self.num_entities, = struct.unpack("<I", f.read(4))
                    print("Number of entities:", self.num_entities)

                    # read entity names
                    for i in range(0, self.num_entities):
                        entity_name_length, = struct.unpack("<I", f.read(4))
                        entity_name = f.read(entity_name_length)
                        print("Entity name:", entity_name)
                        self.entities.append(entity_name.decode("utf-8"))
                      
                if entry == SUPPORTED_ENTRY[2]:  #FRM2
                    # read keyframe time
                    keyframe_time, = struct.unpack("<H", f.read(2))
                    print("Keyframe time:", keyframe_time)

                    # Create a new frame object
                    frame = ANM_FRAME(keyframe_time)

                    # read number of frame data chunks that follow
                    keyframe_chunks, = struct.unpack("<B", f.read(1))
                    print("Keyframe data chunks:", keyframe_chunks)

                    # Read all the chunks
                    for i in repeat(None, keyframe_chunks):
                        # read chunks index
                        keyframe_chunk_index, = struct.unpack("<B", f.read(1))
                        print("Keyframe chunk index:", keyframe_chunk_index)

                        # read chunk type
                        keyframe_chunk_type, = struct.unpack("<H", f.read(2))
                        print("Keyframe chunk type:", hex(keyframe_chunk_type))

                        # Create new frame event
                        frame_event = ANM_FRAME_EVENT(keyframe_chunk_index, keyframe_chunk_type)

                        # Check if this chunk has position data
                        if keyframe_chunk_type & FRAME_TYPE_POSITION:
                            frame_event.properties.append(self.read_position(f))

                        # Check if this chunk has quaternion data
                        if keyframe_chunk_type & FRAME_TYPE_QUATERNION:
                            # Read quaternion data passing a true/false argument telling if it is an inverted one
                            frame_event.properties.append(self.read_quaternion(f, (keyframe_chunk_type & FRAME_TYPE_INVERTED) ))

                        # Print a message if we find one of those strange 4th bit chunks
                        if keyframe_chunk_type & FRAME_TYPE_UNKOWN:
                            print("Unkown frame chunk bit 4 found!")

                        # Check if this chunk has a vertex list
                        if keyframe_chunk_type & FRAME_TYPE_VERTICES:
                            # Read number of bytes of the vertex data
                            bytes, = struct.unpack("<I", f.read(4))
                            print("Number of bytes: %i at %s" % (bytes, hex(f.tell())))

                            # Read some unknown data
                            struct.unpack("f", f.read(4))

                            # Read number of vertices
                            verts, = struct.unpack("<H", f.read(2))
                            print("Number of verts: %i at %s" % (verts, hex(f.tell())))

                            # Read some unkonw data
                            struct.unpack("2x", f.read(2))

                            # Calculate vertex size
                            vertex_size = (int)(bytes / verts)

                            # Read vertices
                            for i in range(0, verts):
                                #f.read(vertex_size)
                                vx,vy,vz,nx,ny,nz,U,V = struct.unpack("ffffffff", f.read(32))
                                #vx,vy,vz,nx,ny,nz,U,V = struct.unpack("ffffffff16x", f.read(48))
                            # Read some unknown data
                            if keyframe_chunk_type & FRAME_TYPE_POSITION:
                                struct.unpack("ffffffff", f.read(32))
                                #struct.unpack("ffffffff16x", f.read(48))
                            else:
                                struct.unpack("ff", f.read(8))

                        # Add event type our frames event list
                        frame.events.append(frame_event)

                    # Add frame to our keyframe list
                    self.keyframes.append(frame)

    def read_position(self, f):
        # Read position
        x, y, z = struct.unpack("fff", f.read(12))
        # Create a new frame position object
        return ANM_FRAME_POSITION(x, y, z)

    def read_quaternion(self, f, inverted):
        import mathutils

        w = x = y = z = 0.0

        # Read quaternion
        x, y, z = struct.unpack("fff", f.read(12))

        # Calculate W
        # xyz = 1.0 - ( (x*x) + (y*y) + (z*z) )
        # if xyz > 0.0:
        #     w = math.sqrt(xyz)
        w = math.sqrt(math.fabs(1.0 - ( (x*x) + (y*y) + (z*z) )))

        # Check if this is an inverted quaternion
        if inverted:
            import pdb
            pdb.set_trace()
            m = Quaternion(w, x, y, z).toMatrix()
            # Return an inverted quaternion
            return ANM_FRAME_QUATERNION(y, -x, w, -z)
        else:
            # Return a normal quaternion
            return ANM_FRAME_QUATERNION(x, y, z, w)
