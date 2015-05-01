# Initial version of this file by Stan Bobovych
# The original version can be found here https://github.com/sbobovyc/GameTools/blob/master/MoW/ply.py

# Further enhancements modifications by Björn Martins Paz

from __future__ import print_function

import struct

# constants
PLYMAGICK = b"EPLYBNDS"
SUPPORTED_ENTRY = [b"SKIN", b"MESH", b"VERT", b"INDX"]
SUPPORTED_MESH = [0x0112, 0x1118]
SUPPORTED_FORMAT = [0x0644, 0x0604, 0x0404, 0x0406, 0x0704, 0x705, 0x0744, 0x0745, 0x0C14, 0x0F14, 0x0F54, 0x0C54]

class PLY:
    def __init__(self, path):
        self.path = path
        self.indeces = []
        self.positions = []
        self.vertex_groups = {}
        self.normals = []
        self.UVs = []
        self.mesh_info = 0x0000
        self.material_info = 0x0000
        self.material_file = None

        self.open(self.path)

    def open(self, peek=False, verbose=False):
        with open(self.path, "rb") as f:
            # read header
            magick, = struct.unpack("8s", f.read(8))
            if magick != PLYMAGICK:
                raise Exception("Unsupported format %s" % magick)
            x1, y1, z1, x2, y2, z2 = struct.unpack("ffffff", f.read(24))
            while True:
                entry, = struct.unpack("4s", f.read(4))
                print("Found entry %s at %s" % (entry, hex(f.tell())) )
                if not(entry in SUPPORTED_ENTRY):
                    raise Exception("Unsupported entry type")
                if entry == SUPPORTED_ENTRY[0]: #SKIN
                    # read the number of skins
                    skins, = struct.unpack("<I", f.read(4))
                    print("Number of skins: %i at %s" % (skins, hex(f.tell())))
                    for i in range(0, skins):
                      skin_name_length, = struct.unpack("B", f.read(1))
                      print("Skin name length:", hex(skin_name_length))
                      skin_name = f.read(skin_name_length)
                      print("Skin name:", skin_name)
                if entry == SUPPORTED_ENTRY[1]: #MESH
                    self.mesh_info, = struct.unpack("<I", f.read(4))
                    # read some unknown data
                    f.read(0x4)
                    triangles, = struct.unpack("<I", f.read(4))
                    print("Number of triangles:",triangles)
                    self.material_info, = struct.unpack("<I", f.read(4))
                    print("Material info:", hex(self.material_info))
                    if self.material_info in SUPPORTED_FORMAT:
                        if self.material_info == 0x0404:
                            pass
                        elif self.material_info == 0x0406:
                            pass
                        elif self.material_info == 0x0C14:
                            pass
                        elif self.material_info == 0x0C54:
                            pass
                        else:
                            color = f.read(0x4) # R G B A
                    else:
                        raise Exception("Unsupported material type")
                    material_name_length, = struct.unpack("B", f.read(1))
                    print("Material name length:", hex(material_name_length))
                    material_file = f.read(material_name_length)
                    print("Material file:", material_file)
                    self.material_file = material_file.decode("utf-8")
                    # read some more unknown data
                    #if self.material_info == 0x0C14 or self.material_info == 0x0F14 or self.material_info == 0x0C54 or self.material_info == 0x0F54:
                    if self.mesh_info == 0x1118:
                        # Read number of entries
                        entries, = struct.unpack("B", f.read(1))
                        # Read unknown entries
                        f.read(entries)
                if entry == SUPPORTED_ENTRY[2]: #VERT
                    verts, = struct.unpack("<I", f.read(4))
                    print("Number of verts: %i at %s" % (verts, hex(f.tell())))
                    self.vertex_description, = struct.unpack("<I", f.read(4))
                    print("Vertex description:", hex(self.vertex_description))
                    index = 0
                    for i in range(0, verts):
                        if self.vertex_description == 0x00010024:
                            vx,vy,vz,nx,ny,nz,U,V = struct.unpack("ffffff4xff", f.read(36))
                        elif self.vertex_description == 0x00070020:
                            vx,vy,vz,nx,ny,nz,U,V = struct.unpack("ffffffff", f.read(32))
                        elif self.vertex_description == 0x00070024:
                            vx,vy,vz,nx,ny,nz,U,V = struct.unpack("ffffff4xff", f.read(36))
                        elif self.vertex_description == 0x00070028:
                            vx,vy,vz,nx,ny,nz,U,V = struct.unpack("ffffff8xff", f.read(40))
                        elif self.vertex_description == 0x00070030:
                            vx,vy,vz,nx,ny,nz,U,V = struct.unpack("ffffffff16x", f.read(48))
                        elif self.vertex_description == 0x00070038:
                            vx,vy,vz,nx,ny,nz,U,V = struct.unpack("ffffffff24x", f.read(56))
                        else:
                            raise Exception("Unknown format: %s" % hex(self.vertex_description))
                        if verbose:
                            print("Vertex %i: " % i,vx,vy,vz)
                        self.positions.append((vx,vy,vz))
                        # if vg not in self.vertex_groups:
                        #     print('Creating vertex group', vg)
                        #     self.vertex_groups[vg] = []
                        # self.vertex_groups[vg].append(index)
                        self.normals.append((nx,ny,nz))
                        self.UVs.append((U,1-V))
                        index += 1
                    print("Vertex info ends at:",hex(f.tell()))
                if entry == SUPPORTED_ENTRY[3]: #INDX
                    idx_count, = struct.unpack("<I", f.read(4))
                    print("Indeces:", idx_count)
                    for i in range(0, int(idx_count/3)):
                        i0,i1,i2 = struct.unpack("<HHH", f.read(6))
                        if verbose:
                            print("Face %i:" % i,i0,i1,i2)
                        if self.material_info == 0x0744 or self.material_info == 0x0c54:
                          self.indeces.append((i0,i1,i2))
                          #self.indeces.append((i2,i1,i0))
                        else:
                          #self.indeces.append((i0,i1,i2))
                          self.indeces.append((i2,i1,i0))
                    print("Indces end at", hex(f.tell()-1))
                    break

    def dump(self, outfile):
        print("Dumping to OBJ")
        with open(outfile, "wb") as f:
            for p in self.positions:
                f.write('{:s} {:f} {:f} {:f}\n'.format("v", *p))
            for UV in self.UVs:
                u = UV[0]
                v = 1.0 - UV[1]
                f.write('{:s} {:f} {:f}\n'.format("vt", u, v))
            for n in self.normals:
                f.write('{:s} {:f} {:f} {:f}\n'.format("vn", *n))
            for idx in self.indeces:
                new_idx = map(lambda x: x+1, idx)
                # change vertex index order by swapping the first and last indeces
                f.write('{:s} {:d}/{:d}/{:d} {:d}/{:d}/{:d} {:d}/{:d}/{:d}\n'.format("f", new_idx[2], new_idx[2],
                new_idx[2], new_idx[1], new_idx[1], new_idx[1], new_idx[0], new_idx[0], new_idx[0]))                