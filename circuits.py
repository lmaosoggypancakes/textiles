from typing import *
from svg import *
from helpers import * # mainly just using create_r_zigzag
from embroidery import export_svg_to_brother

class Footprint:
    def __init__(self, paths: List[List[List[List[int|float]]]], x_range: int|float, y_range: int|float, pins: List[List[int|float]]):
        """
        Represents the visual footprint of a given schematic (resistor, chip, whatever)
        """
        # if len(paths) == 0:
            # raise Exception("empty footprint")
        # for layer in paths:
        #     for path in layer:
        #         for (x,y) in path:
        #             if x < 0 or x > x_range or y < 0 or y > y_range:
        #                 raise Exception("path point out of bounds: " + (x,y))

        # for (x,y) in pins:
        #     if x < 0 or x > x_range or y < 0 or y > y_range:
        #         raise Exception("pin out of bounds: " + (x,y))

        self.paths = paths
        self.x_range = x_range
        self.y_range = y_range
        self.pins = pins

    def serialize(self):
        return {
            "x_range": self.x_range,
            "y_range": self.y_range,
            "pins": self.pins,
            "paths": self.paths
        }

 
class CircuitComponent:
    def __init__(self, ref: str, footprint: Footprint, name: str, pins: int, via=False, layers=[0]):
        if ref == "":
            raise Exception("no ref")
        if name == "":
            raise Exception("no name")
        if pins <= 0 and not via:
            raise Exception("a module needs at least 1 pin if it's not a via")
        if len(footprint.pins) != pins:
            raise Exception("footprint pins and module pins don't match")
        if len(layers) == 0:
            raise Exception("a module must be on a layer")
        if len(layers) == 1 and via:
            raise Exception("the whole point of a via is that it exists in multiple layers")
        self.ref = ref
        self.footprint = footprint
        self.name = name
        self.pins = pins
        self.via = via
        self.layers = layers

    def __eq__(self, other):
        return self.ref == other.ref # REFS SHOULD BE UNIQUE

    def serialize(self):
        return {
            "ref": self.ref,
            "footprint": self.footprint.serialize(),
            "name": self.name,
            "pins": self.pins,
            "via": self.via,
            "layers": self.layers
        }

class Physical:
    def __init__(self, c, x, y):
        self.c = c
        self.x = x
        self.y = y

class Circuit:
    def __init__(self, modules: List[CircuitComponent]):
        refs = set(map(lambda m: m.ref, modules))
        if len(refs) != len(modules):
            raise Exception("duplicate refs somewhere. fix.")
        self.modules = modules
        self.graph = [None]*len(self.modules)
        for i in range(len(self.graph)):
            self.graph[i] = [None]*len(self.modules)

    def connect(self, a: CircuitComponent, b: CircuitComponent, i: int, j: int, vias=[]):
        """
        Connect modules `a` and `b` by pin `i` of `a` to pin `j` of `b`, with given via points.
        `a` and `b` must not be via points
        """
        a_i = self.modules.index(a)
        b_i = self.modules.index(b)
        if a.via or b.via:
            raise Exception("can you fucking read")
        if len(a.layers) != 1 or len(b.layers) != 1:
            raise Exception("this should not happen")
        if a.layers[0] != b.layers[0] and len(vias) == 0:
            raise Exception("you can't connect modules in different layers without vias dumbass")

        self.graph[a_i][b_i] = [i, *vias, j]
        self.graph[b_i][a_i] = [j, *reversed(vias), i]

    def connections_for_modules(self, a: CircuitComponent):
        """
        Get all the connections that go to/from module a.
        Returns {i, *V, j, b}[] where i is pin i of module a, V is any via points, to pin j of module b
        i, j are pins, ...V and j are module indexes.
        min length of any set is 3. (i,j,V=[],b)
        """
        idx = self.modules.index(a)
        ret = []
        for j in range(self.graph):
            if self.graph[idx][j]:
                ret.append([*self.graph[idx][j], j])
        return ret

    def __eq__(self, other):
        return self.modules == other.modules

def render_circuit(circuit: Circuit) -> SVG :
    svg = SVG(800, 800)
    circle_radius = 300
    for (i, m) in enumerate(circuit.modules):
        # place them along a circle
        # first, place a circle representing the center of each module:
        angle = 2 * math.pi * i / len(circuit.modules)
        x = 400+circle_radius*math.cos(angle)
        y = 400+circle_radius*math.sin(angle)
        svg.circle(x, y, 10, "red")
        svg.text(x,y-20, m.name)
        for p in m.footprint.paths:
            # render each path with a center of (x,y)
            # so, the path should take up the space defined by
            # (x-x_range/2, x+_range/2) and (y-y_range/2, y+y_range/2)
            inst = []
            for (i, (x_p, y_p)) in enumerate(p):
                if i == 0: # M and L are just SVG things for move to/line-to (can move everything to one path as well)
                    inst.append((M, x-m.footprint.x_range+x_p, y-m.footprint.y_range+y_p))
                else:
                    inst.append((L, x-m.footprint.x_range+x_p, y-m.footprint.y_range+y_p))
            svg.path(inst, "green")
        
        for (x_p, y_p) in m.footprint.pins:
            svg.circle(x-m.footprint.x_range+x_p, y-m.footprint.y_range+y_p, 5, "white");
    
    for (i, row) in enumerate(circuit.graph):
        for (j, c) in enumerate(row):
            if c is not None:
                # connection between [i,j] exists
                # TODO: handle pins
                angle1 = 2 * math.pi * i / len(circuit.modules)
                xa = 400+circle_radius*math.cos(angle1)
                ya = 400+circle_radius*math.sin(angle1)

                angle2 = 2 * math.pi * j / len(circuit.modules)
                xb = 400+circle_radius*math.cos(angle2)
                yb = 400+circle_radius*math.sin(angle2)
                svg.path([(M, xa, ya), (L, xb, yb)], stroke="purple")
    return svg

class Module:
    def __init__(self, circuit: Circuit, pins=8):
        # the i'th pin for any 0<=i<=pins has relative polar position (r, 2i/8*i)
        self.pins = pins
        self.pcs = []
        circle_radius = 300 
        self.circuit = circuit
        # self.pins_in_use = []
    
        for (i, m) in enumerate(circuit.modules):
            # place them along a circle
            # first, place a circle representing the center of each module:
            angle = 2 * math.pi * i / len(circuit.modules)
            x = 400+circle_radius*math.cos(angle)
            y = 400+circle_radius*math.sin(angle)
            self.pcs.append(Physical(m, x, y))
    
    @staticmethod
    def pin_for(pin):
        if not 0<=pin<8:
            raise Exception("dude stop")
        if pin == 0:
            return (15, 26)
        if pin == 1:
            return (21, 31)
        if pin == 2:
            return (27,31)
        if pin == 3:
            return (34, 26)
        if pin == 4:
            return (33, 10)
        if pin == 5:
            return (27, 4)
        if pin == 6:
            return (21, 4)
        if pin == 7:
            return (15, 9)

    def __eq__(self, other):
        return self.circuit == other.circuit

class Schematic:
    """
    a 'schematic' is defined to be a graph of modules.
    a 'module' is defined to be a circuit with spacial constraints and exit pins (a lilypad)
    a 'circuit' is a graph of electrical components
    an 'electrical component' is defined to be a representation with a ref(id), footprint, and pin declaration
    """
    def __init__(self, modules: List[Module]):
        self.modules = modules
        self.graph = [None]*len(self.modules)
        self.__physicals = []
        circle_radius = 100 
        # self.pins_in_use = []
    
        for (i, m) in enumerate(modules):
            # place them along a circle
            # first, place a circle representing the center of each module:
            angle = 2 * math.pi * i / len(self.modules)
            x = 256+circle_radius*math.cos(angle)
            y = 256+circle_radius*math.sin(angle)
            self.__physicals.append(Physical(m, x, y))

        for i in range(len(self.graph)):
            self.graph[i] = [None]*len(self.modules)

    def traces(self, svg=None):
        if not svg:
            svg = SVG(512, 512)
        done = []
        for (i, p) in enumerate(self.__physicals):
            # svg.circle(p.x,p.y,5,"red")
            s = "{"
            for mod in p.c.circuit.modules:
                s += mod.ref + ", "
            s+="}"
            svg.image(p.x-9,p.y-7,200,160,"paths/module.svg")
            svg.text(p.x,p.y-10,s)
        for lilypad in self.__physicals:
            for a in self.connections_for_modules(lilypad.c):
                i = a[0]
                j = a[1]
                b = self.__physicals[a[2]]
                a_pins = Module.pin_for(i)
                b_pins = Module.pin_for(j)
                lilypad_x = lilypad.x + a_pins[0]
                lilypad_y = lilypad.y + a_pins[1]
                b_x = b.x + b_pins[0]
                b_y = b.y + b_pins[1]
                if (lilypad, b) not in done and (b, lilypad_y) not in done:
                    create_r_zigzag((lilypad_x, lilypad_y), (b_x, b_y), 1.2, 10, svg)
                    done.append((b, lilypad))
                print(done)
        return svg

    def mountpoints(self, svg=None):
        if not svg:
            svg = SVG(512, 512)
        for (i, p) in enumerate(self.__physicals):
            # svg.circle(p.x,p.y,5,"red")
            s = "{"
            for mod in p.c.circuit.modules:
                s += mod.ref + ", "
            s+="}"
            # AHHHHH
            x = p.x+12
            y1 = p.y+5
            y2 = p.y+30
            svg.image(p.x-9,p.y-7,200,160,"paths/module.svg") # this is the center
            svg.path([(M, x, y1), (L,x, y2), (L, x,y1), (L, x, y2), (L, x, y1), (L, x, y2)])
            x = p.x-9+50
            y1 = p.y+5
            y2 = p.y+30
            svg.path([(M, x, y1), (L, x, y2), (L, x, y1), (L, x, y2), (L, x, y1), (L, x, y2)])
            svg.text(p.x,p.y-10,s)
        return svg
        
       
    def render(self):
        svg = SVG(512, 512)
        return self.mountpoints(self.traces(svg))


    def connect(self, a: Module, b: Module, i: int, j: int):
        """
        Connect modules `a` and `b` by pin `i` of `a` to pin `j` of `b`, with given via points.
        `a` and `b` must not be via points
        """
        a_i = self.modules.index(a)
        b_i = self.modules.index(b)

        self.graph[a_i][b_i] = [i, j]
        self.graph[b_i][a_i] = [j, i]

    def connections_for_modules(self, a: Module):
        """
        Get all the connections that go to/from module a.
        Returns {i, *V, j, b}[] where i is pin i of module a, V is any via points, to pin j of module b
        i, j are pins, ...V and j are module indexes.
        min length of any set is 3. (i,j,V=[],b)
        """
        idx = self.modules.index(a)
        ret = []
        for j in range(len(self.graph)):
            if self.graph[idx][j]:
                ret.append([*self.graph[idx][j], j])
        return ret

if __name__ == "__main__":

    # === Step 0: create circuit/module groupings ===

    # low-level footprints and components
    res_fp = Footprint(
        [[]], 50, 50, [[25,45], [5, 45]]
    )
    res = CircuitComponent("R1", res_fp, "Resistor", 2)

    pow_fp = Footprint(
        [[]], 50, 50, [[45, 25]]
    )
    power = CircuitComponent("VCC", pow_fp, "+5V", 1)

    gnd_fp = Footprint(
        [[]], 50, 50, [[25, 45]]
    )
    ground = CircuitComponent("GND", gnd_fp, "GND", 1)

    # circuits from these components, which go into one lilypad by themselves (for now)
    res_module = Module(Circuit([res]))
    pow_module = Module(Circuit([power]))    
    gnd_module = Module(Circuit([ground]))
    
    s = Schematic([res_module, pow_module, gnd_module])
    s.connect(res_module, pow_module, 1, 4);
    s.connect(res_module, gnd_module, 0, 0)

    # === Step 1: mountpoints ===
    
    mountpoints = s.mountpoints()
    export_svg_to_brother(mountpoints, "mountpoints.pes")
    # === Step 2: traces === 

    traces = s.traces()
    export_svg_to_brother(traces, "traces.pes")

    # for viewing svg
    traces.save("full.svg")

