#How to use this thing:
#- hit run script
#- in 3d view, hit space to get the menu and search for "pioneer" (the operator is called Export to Pioneer)
#- it will export the currently supported features to clipboard which you can then paste to your ship lua
#
# Currently supported:
# Thrusters. Use "Empty" objects to position them. Name must begin with "thruster". In empty object properties
# change display type to "arrow" to better see where the thruster is pointing. "Size" parameter will determine
# the flare size. To make a thruster linear only add a custom property called "linear" (or just copy the example
# thrusters around)
#
# Gun mounts:
# Use empties (or any object, actually), with a name beginning "gunmount". Position and direction are taken from the
# object location and angle. "Arrow" display type is again helpful here.
#
# Lights:
# Use empties, or any objects. Naming does not matter. Instead, lights are collected based on what groups they are
# in. Supported group names are:
# navlights_collision
# navlights_red
# navlights_green
import bpy
from mathutils import Vector, Quaternion

template = """--exported by funky exporter
define_model(NAME, {
    info = { },
    static = function(lod)
        --set material
        --use material
        --load_obj
        --thrusters
        --lights
    end,
})"""

#some tiny internal classes
class PiVector:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

    def __str__(self):
        return "v(%.3f, %.3f, %.3f)" % (self.x, self.y, self.z)

#blender location to pioneer position       
class Pos(PiVector):
    def __init__(self, bPos):
        self.x = bPos.x
        self.y = bPos.z
        self.z = bPos.y * -1.0

class Dir(PiVector):
    def __init__(self, obj):
        #making a lot of assumptions here
        #euler XYZ to Pioneer -> X,Z,-Y
        poo = obj.rotation_euler.to_matrix()[2]
        self.x = poo[0]
        self.y = poo[2]
        self.z = poo[1] * -1.0
    
class Thruster():
    def __init__(self, empty):
        self.pos = Pos(empty.location)
        self.dir = Dir(empty)
        self.size = empty.empty_draw_size #probably needs to be scaled a bit
        self.linear = empty["linear"] if "linear" in empty else 0.0

    def __str__(self):
        return "thruster(%s, %s, %.2f, %s)" % (self.pos.__str__(), self.dir.__str__(),
            self.size, 'true' if self.linear > 0.0 else 'false')

class Gunmount():
    def __init__(self, empty):
        self.pos = Pos(empty.location)
        self.dir = Dir(empty)

    def __str__(self):
        return "{ %s, %s }" % (self.pos.__str__(), self.dir.__str__())

class Light():
    def __init__(self, empty):
        self.pos = Pos(empty.location)

    def __str__(self):
        return self.pos.__str__()
        #return "navlight(%s)" % (self.pos.__str__())

class LightGroup():
    def __init__(self):
        self.lights = []

    def add(self, obj):
        self.lights.append(Light(obj))

    def __str__(self):
        result = "{"
        for l in self.lights:
            result += l.__str__() + ", "
        result += "}"
        return result

class pioneerOperator(bpy.types.Operator):
    bl_idname = "export.pioneer"
    bl_label = "Export to Pioneer"
    myfilename = ""
    
    def execute(self, context):
        #first, collect objects and organize them internally (by lods probably?)
        #then do dump separately
        print('\n')
        self.collect()
        self.write()
        return {'FINISHED'}
    
    def collect(self):
        self.thrusters       = []
        self.gunmounts       = []
        self.lights          = dict(
            coll  = LightGroup(),
            red   = LightGroup(),
            green = LightGroup()
        )
        self.dumpEmpties()

    def write(self):
        result = ""
        if len(self.thrusters) > 0:
            result += "--thrusters for static section\n"
            for toot in self.thrusters:
                result += toot.__str__() + "\n"
        
        if len(self.gunmounts) > 0:
            mounts = "\n--gun_mounts for ship info\n"
            mounts += "gun_mounts = {\n"
            for gun in self.gunmounts:
                mounts += "\t%s,\n" % gun.__str__()
            mounts += "}\n"
            result += mounts

        result += "\n--lights for dynamic section\n"
        result += "navigation_lights(\n\t%s,\n\t%s,\n\t%s\n)" % (
            self.lights["coll"].__str__(),
            self.lights["red"].__str__(),
            self.lights["green"].__str__())
        #for l in self.lights:
        #    result += l.__str__() + "\n"
        bpy.data.window_managers[0].clipboard = result
        #navigation_lights(collArr, redArr, greenArr)
    
    def dumpEmpties(self):
        #collect thrusters first
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY':
                if obj.name.startswith('thruster'): #good enough
                    self.thrusters.append(Thruster(obj))
                if obj.name.startswith('gunmount'):
                    self.gunmounts.append(Gunmount(obj))
                #elif obj.name.startswith('light'):
                #    self.lights.append(Light(obj))
        #things organized by group
        for grp in bpy.data.groups:
            if grp.name.startswith('navlights'):
                #doesn't matter if these are empties or not
                self.getLightsFromGroup(grp)

    #one light can be in many groups, this is fine
    def getLightsFromGroup(self, group):
        for obj in group.objects:
            if group.name == 'navlights_collision':
                self.lights["coll"].add(obj)
            if group.name == 'navlights_red':
                self.lights["red"].add(obj)
            if group.name == 'navlights_green':
                self.lights["green"].add(obj)


# register
def register():
    bpy.utils.register_class(pioneerOperator)

# unregister
def unregister():
    bpy.utils.unregister_class(pioneerOperator)

if __name__ == "__main__":
    register()